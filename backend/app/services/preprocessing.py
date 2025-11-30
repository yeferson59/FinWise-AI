import cv2
import numpy as np
from pathlib import Path
from typing import Any
from PIL import Image
from rembg import remove
from app.ocr_config import PreprocessingConfig, DocumentType, get_profile
from app.utils.image import (
    load_image,
    to_grayscale,
    save_temp_image,
)

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


# ============================================================================
# ENHANCED PREPROCESSING CONSTANTS
# ============================================================================

# Optimal DPI for OCR (300 DPI is standard for document scanning)
OPTIMAL_DPI = 300
MIN_DPI_ESTIMATE = 150

# Minimum dimensions for good OCR
MIN_WIDTH_FOR_OCR = 400
MIN_HEIGHT_FOR_OCR = 300


def scale_image(image: Any, config: PreprocessingConfig) -> tuple[Any, float]:
    """
    Scale image if it's too small for better OCR accuracy.
    Returns the scaled image and the scale factor used.
    """
    height, width = image.shape[:2]
    min_height = config.scale_min_height

    if height < min_height:
        scale_factor = min_height / height
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        scaled_image = cv2.resize(
            image, (new_width, new_height), interpolation=cv2.INTER_CUBIC
        )
        return scaled_image, scale_factor

    return image, 1.0


def remove_background(image: Any) -> Any:
    """
    Remove background from an image using rembg library.
    This helps improve OCR accuracy by eliminating distracting background elements.

    Args:
        image: Input image as numpy array (BGR format from cv2)

    Returns:
        Image with background removed as numpy array (BGR format)
    """
    try:
        # Convert BGR (OpenCV) to RGB (PIL)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)

        # Remove background
        output_pil = remove(pil_image)

        # Convert back to numpy array (RGBA)
        output_rgba = np.array(output_pil)

        # Check if the image has an alpha channel
        if output_rgba.shape[2] == 4:
            # Extract alpha channel
            alpha = output_rgba[:, :, 3]

            # Create a white background
            white_background = np.ones_like(output_rgba[:, :, :3]) * 255

            # Blend the image with white background using alpha channel
            alpha_3channel = np.stack([alpha, alpha, alpha], axis=2) / 255.0
            result_rgb = (
                output_rgba[:, :, :3] * alpha_3channel
                + white_background * (1 - alpha_3channel)
            ).astype(np.uint8)
        else:
            result_rgb = output_rgba[:, :, :3]

        # Convert RGB back to BGR for OpenCV
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)

        return result_bgr
    except Exception as e:
        # If background removal fails, return the original image
        print(f"Background removal failed: {e}. Using original image.")
        return image


def deskew_image(image: Any) -> Any:
    """
    Correct the skew of an image using contour detection for better accuracy.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use binary threshold to find contours
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find all contours
    coords = cv2.findNonZero(thresh)

    if coords is not None and len(coords) > 0:
        # Get the minimum area rotated rectangle
        angle = cv2.minAreaRect(coords)[-1]

        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Only rotate if angle is significant (more than 0.5 degrees)
        if abs(angle) > 0.5:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed_image = cv2.warpAffine(
                image,
                rotation_matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return deskewed_image

    return image


def preprocess_image(
    filepath: str,
    document_type: DocumentType | None = None,
    config: PreprocessingConfig | None = None,
    save_to_temp: bool = True,
) -> str:
    """
    Preprocess an image for OCR with configurable settings.
    Enhanced version with better noise reduction and text enhancement.

    Args:
        filepath: Path to the image file
        document_type: Type of document (receipt, invoice, etc.)
        config: Custom preprocessing configuration (overrides document_type)
        save_to_temp: If True, save to temporary directory instead of alongside original

    Returns:
        Path to the preprocessed image
    """
    image = load_image(filepath)

    # Get configuration
    if config is None:
        if document_type is not None:
            profile = get_profile(document_type)
            config = profile.preprocessing_config
        else:
            # Use default config
            profile = get_profile(DocumentType.GENERAL)
            config = profile.preprocessing_config

    # Step 1: Remove background if enabled (do this early to eliminate noise)
    if config.enable_background_removal:
        image = remove_background(image)

    # Step 2: Scale image if too small (improves OCR accuracy)
    if config.scale_min_height > 0:
        image, _ = scale_image(image, config)

    # Step 3: Deskew
    if config.enable_deskew:
        image = deskew_image(image)

    # Step 4: Convert to Grayscale
    gray = to_grayscale(image)

    # Step 5: Enhanced noise removal with bilateral filter (preserves edges better)
    if config.denoise_strength > 0:
        # First pass: bilateral filter (edge-preserving)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        # Second pass: Non-local means for remaining noise
        denoised = cv2.fastNlMeansDenoising(
            denoised,
            None,
            h=config.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21,
        )
    else:
        denoised = gray

    # Step 6: Enhance Contrast with CLAHE (improved parameters)
    if config.enable_clahe:
        # Use smaller tile grid for better local contrast
        clahe = cv2.createCLAHE(
            clipLimit=config.clahe_clip_limit,
            tileGridSize=(4, 4),  # Smaller tiles for finer detail
        )
        enhanced = clahe.apply(denoised)
    else:
        enhanced = denoised

    # Step 7: Apply Gaussian blur to reduce high-frequency noise before thresholding
    blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

    # Step 8: Adaptive Thresholding (improved binary filter)
    thresh = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_threshold_block_size,
        config.adaptive_threshold_c,
    )

    # Step 9: Morphological Operations (optional) - improved sequence
    if config.enable_morphology:
        kernel = np.ones(config.morphology_kernel_size, np.uint8)
        # First close small gaps in characters
        final_image = cv2.morphologyEx(
            thresh, cv2.MORPH_CLOSE, kernel, iterations=config.morphology_iterations
        )
        # Then open to remove small noise spots
        noise_kernel = np.ones((2, 2), np.uint8)
        final_image = cv2.morphologyEx(
            final_image, cv2.MORPH_OPEN, noise_kernel, iterations=1
        )
    else:
        final_image = thresh

    # Save Preprocessed Image
    if save_to_temp:
        # Create a temporary file with the same extension
        original_path = Path(filepath)
        suffix = original_path.suffix if original_path.suffix else ".png"
        preprocessed_path = save_temp_image(
            final_image, suffix=f"_preprocessed{suffix}", prefix="ocr_"
        )
    else:
        # Save alongside original (legacy behavior)
        preprocessed_path = filepath.replace(".", "_preprocessed.")
        cv2.imwrite(preprocessed_path, final_image)

    return preprocessed_path


def preprocess_image_simple(filepath: str) -> str:
    """
    Simple preprocessing with default general settings.
    This is the backward-compatible version.
    """
    return preprocess_image(
        filepath, document_type=DocumentType.GENERAL, save_to_temp=False
    )


# ============================================================================
# PHASE 2: ADVANCED PREPROCESSING IMPROVEMENTS
# ============================================================================


def multi_binarization(gray_image: np.ndarray) -> list[tuple[np.ndarray, str]]:
    """
    Generate multiple binarized versions of an image using different techniques.

    This allows trying multiple approaches and selecting the best result.

    Args:
        gray_image: Grayscale image as numpy array

    Returns:
        List of tuples (binarized_image, method_name)
    """
    results: list[tuple[np.ndarray, str]] = []

    # 1. Adaptive Gaussian Threshold (current default)
    try:
        adaptive_gaussian = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
        )
        results.append((adaptive_gaussian, "adaptive_gaussian"))
    except Exception as e:
        print(f"Adaptive Gaussian failed: {e}")

    # 2. Adaptive Mean Threshold
    try:
        adaptive_mean = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 5
        )
        results.append((adaptive_mean, "adaptive_mean"))
    except Exception as e:
        print(f"Adaptive Mean failed: {e}")

    # 3. Otsu's Binarization (good for bimodal histograms)
    try:
        _, otsu = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results.append((otsu, "otsu"))
    except Exception as e:
        print(f"Otsu failed: {e}")

    # 4. Sauvola Binarization (better for documents with shadows/uneven illumination)
    try:
        # Sauvola algorithm implementation
        window_size = 25
        k = 0.5
        R = 128

        # Calculate local mean and std
        mean = cv2.boxFilter(
            gray_image.astype(np.float32), -1, (window_size, window_size)
        )
        sqr_mean = cv2.boxFilter(
            gray_image.astype(np.float32) ** 2, -1, (window_size, window_size)
        )
        std = np.sqrt(sqr_mean - mean**2)

        # Sauvola threshold
        threshold = mean * (1 + k * ((std / R) - 1))
        sauvola = np.where(gray_image > threshold, 255, 0).astype(np.uint8)
        results.append((sauvola, "sauvola"))
    except Exception as e:
        print(f"Sauvola failed: {e}")

    # 5. Simple global threshold with blur preprocessing
    try:
        blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
        _, simple = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
        results.append((simple, "simple_threshold"))
    except Exception as e:
        print(f"Simple threshold failed: {e}")

    return results  # type: ignore[return-value]


def detect_text_orientation(image: np.ndarray) -> int:
    """
    Detect text orientation in the image (0, 90, 180, 270 degrees).

    Uses Tesseract's OSD (Orientation and Script Detection) when available,
    falls back to edge detection analysis.

    Args:
        image: Input image as numpy array (BGR format)

    Returns:
        Rotation angle needed (0, 90, 180, or 270 degrees)
    """
    # Try Tesseract OSD first (most accurate)
    if TESSERACT_AVAILABLE:
        try:
            # Convert to PIL Image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            # Get orientation and script detection
            osd = pytesseract.image_to_osd(
                pil_image, output_type=pytesseract.Output.DICT
            )
            rotation = osd.get("rotate", 0)  # type: ignore[union-attr]

            # Normalize to 0, 90, 180, 270
            rotation = int(rotation)
            if rotation not in [0, 90, 180, 270]:
                rotation = (rotation // 90) * 90

            return rotation
        except Exception as e:
            print(f"Tesseract OSD failed: {e}, using fallback method")

    # Fallback: Edge-based orientation detection
    try:
        gray = to_grayscale(image)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is not None and len(lines) > 0:
            angles = []
            for line in lines[: min(20, len(lines))]:  # Use top 20 lines
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                angles.append(angle)

            if angles:
                # Calculate median angle
                angle_median = np.median(angles)

                # Map to nearest 90-degree rotation
                if -45 <= angle_median < 45:
                    return 0
                elif 45 <= angle_median < 135:
                    return 90
                elif angle_median >= 135 or angle_median < -135:
                    return 180
                else:
                    return 270
    except Exception as e:
        print(f"Edge-based orientation detection failed: {e}")

    # Default: no rotation
    return 0


def rotate_image_to_correct_orientation(image: np.ndarray) -> tuple[np.ndarray, int]:
    """
    Detect and correct image orientation automatically.

    Args:
        image: Input image as numpy array (BGR format)

    Returns:
        Tuple of (rotated_image, rotation_applied)
    """
    rotation = detect_text_orientation(image)

    if rotation == 0:
        return image, 0

    # Get image dimensions
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    # Create rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, rotation, 1.0)

    # Calculate new dimensions for 90/270 rotations
    if rotation in [90, 270]:
        # Swap dimensions
        new_w, new_h = h, w
        # Adjust rotation matrix for dimension swap
        cos = np.abs(rotation_matrix[0, 0])
        sin = np.abs(rotation_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
    else:
        # 180-degree rotation
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    return rotated, rotation


def preprocess_with_multiple_binarizations(
    filepath: str,
    document_type: DocumentType | None = None,
    config: PreprocessingConfig | None = None,
) -> list[tuple[str, str]]:
    """
    Preprocess image using multiple binarization techniques.

    Returns multiple preprocessed versions for testing different approaches.

    Args:
        filepath: Path to the image file
        document_type: Type of document
        config: Custom preprocessing configuration

    Returns:
        List of tuples (preprocessed_path, method_name)
    """
    image = load_image(filepath)

    # Get configuration
    if config is None:
        if document_type is not None:
            profile = get_profile(document_type)
            config = profile.preprocessing_config
        else:
            profile = get_profile(DocumentType.GENERAL)
            config = profile.preprocessing_config

    # Apply common preprocessing steps
    if config.enable_background_removal:
        image = remove_background(image)

    if config.scale_min_height > 0:
        image, _ = scale_image(image, config)

    if config.enable_deskew:
        image = deskew_image(image)

    # Convert to grayscale
    gray = to_grayscale(image)

    # Apply denoising
    if config.denoise_strength > 0:
        denoised = cv2.fastNlMeansDenoising(
            gray,
            None,
            h=config.denoise_strength,
            templateWindowSize=7,
            searchWindowSize=21,
        )
    else:
        denoised = gray

    # Apply CLAHE
    if config.enable_clahe:
        clahe = cv2.createCLAHE(clipLimit=config.clahe_clip_limit, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
    else:
        enhanced = denoised

    # Generate multiple binarizations
    binarizations = multi_binarization(enhanced)

    # Save each version to temporary file
    results = []
    for bin_image, method_name in binarizations:
        # Apply morphological operations if enabled
        if config.enable_morphology:
            kernel = np.ones(config.morphology_kernel_size, np.uint8)
            final_image = cv2.morphologyEx(
                bin_image,
                cv2.MORPH_CLOSE,
                kernel,
                iterations=config.morphology_iterations,
            )
        else:
            final_image = bin_image

        # Save to temporary file
        temp_path = save_temp_image(
            final_image, suffix=f"_{method_name}.png", prefix="ocr_multi_"
        )
        results.append((temp_path, method_name))

    return results


def cleanup_temp_file(file_path: str) -> None:
    """
    Safely clean up a temporary file.

    Args:
        file_path: Path to the file to delete

    Note:
        This function does not raise exceptions if the file doesn't exist
        or cannot be deleted, to prevent test failures.
    """
    if not file_path:
        return

    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
    except Exception:
        # Silently ignore cleanup errors to prevent test failures
        pass

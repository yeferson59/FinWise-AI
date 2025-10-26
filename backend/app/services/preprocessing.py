import cv2
import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Any
from PIL import Image
from rembg import remove
from app.ocr_config import PreprocessingConfig, DocumentType, get_profile


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

    Args:
        filepath: Path to the image file
        document_type: Type of document (receipt, invoice, etc.)
        config: Custom preprocessing configuration (overrides document_type)
        save_to_temp: If True, save to temporary directory instead of alongside original

    Returns:
        Path to the preprocessed image
    """
    image = cv2.imread(filepath)
    if image is None:
        if os.path.exists(filepath):
            raise ValueError("Invalid image file: file exists but cannot be read as image")
        else:
            raise ValueError("Invalid image file or file does not exist.")

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
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 5: Noise Removal
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

    # Step 6: Enhance Contrast with CLAHE
    if config.enable_clahe:
        clahe = cv2.createCLAHE(clipLimit=config.clahe_clip_limit, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
    else:
        enhanced = denoised

    # Step 7: Adaptive Thresholding (improved binary filter)
    thresh = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_threshold_block_size,
        config.adaptive_threshold_c,
    )

    # Step 8: Morphological Operations (optional)
    if config.enable_morphology:
        kernel = np.ones(config.morphology_kernel_size, np.uint8)
        final_image = cv2.morphologyEx(
            thresh, cv2.MORPH_CLOSE, kernel, iterations=config.morphology_iterations
        )
    else:
        final_image = thresh

    # Save Preprocessed Image
    if save_to_temp:
        # Create a temporary file with the same extension
        original_path = Path(filepath)
        suffix = original_path.suffix if original_path.suffix else ".png"
        
        # Create temp file with delete=False so we can return the path
        temp_fd, preprocessed_path = tempfile.mkstemp(
            suffix=f"_preprocessed{suffix}", 
            prefix="ocr_"
        )
        os.close(temp_fd)  # Close file descriptor as cv2 will write to path
    else:
        # Save alongside original (legacy behavior)
        preprocessed_path = filepath.replace(".", "_preprocessed.")
    
    _ = cv2.imwrite(preprocessed_path, final_image)

    return preprocessed_path


def preprocess_image_simple(filepath: str) -> str:
    """
    Simple preprocessing with default general settings.
    This is the backward-compatible version.
    """
    return preprocess_image(filepath, document_type=DocumentType.GENERAL, save_to_temp=False)


def cleanup_temp_file(filepath: str) -> None:
    """
    Remove a temporary file if it exists.
    
    Args:
        filepath: Path to the file to remove
    """
    try:
        if filepath and os.path.exists(filepath):
            os.unlink(filepath)
    except Exception as e:
        # Log but don't fail if cleanup doesn't work
        print(f"Warning: Failed to cleanup temp file {filepath}: {e}")

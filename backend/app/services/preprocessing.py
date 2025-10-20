import cv2
import numpy as np
from typing import Any
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
) -> str:
    """
    Preprocess an image for OCR with configurable settings.

    Args:
        filepath: Path to the image file
        document_type: Type of document (receipt, invoice, etc.)
        config: Custom preprocessing configuration (overrides document_type)

    Returns:
        Path to the preprocessed image
    """
    image = cv2.imread(filepath)
    if image is None:
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

    # Step 1: Scale image if too small (improves OCR accuracy)
    if config.scale_min_height > 0:
        image, _ = scale_image(image, config)

    # Step 2: Deskew
    if config.enable_deskew:
        image = deskew_image(image)

    # Step 3: Convert to Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 4: Noise Removal
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

    # Step 5: Enhance Contrast with CLAHE
    if config.enable_clahe:
        clahe = cv2.createCLAHE(clipLimit=config.clahe_clip_limit, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
    else:
        enhanced = denoised

    # Step 6: Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        config.adaptive_threshold_block_size,
        config.adaptive_threshold_c,
    )

    # Step 7: Morphological Operations (optional)
    if config.enable_morphology:
        kernel = np.ones(config.morphology_kernel_size, np.uint8)
        final_image = cv2.morphologyEx(
            thresh, cv2.MORPH_CLOSE, kernel, iterations=config.morphology_iterations
        )
    else:
        final_image = thresh

    # Save Preprocessed Image
    preprocessed_path = filepath.replace(".", "_preprocessed.")
    _ = cv2.imwrite(preprocessed_path, final_image)

    return preprocessed_path


def preprocess_image_simple(filepath: str) -> str:
    """
    Simple preprocessing with default general settings.
    This is the backward-compatible version.
    """
    return preprocess_image(filepath, document_type=DocumentType.GENERAL)

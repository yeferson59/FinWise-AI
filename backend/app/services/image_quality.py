"""
Image Quality Assessment and Auto-correction Module
Analyzes image quality and applies automatic corrections for better OCR results.
"""

import cv2
import numpy as np
from typing import Any
from app.utils.image import load_image, to_grayscale


def assess_image_quality(image_path: str) -> dict[str, Any]:
    """
    Analyzes image quality and provides recommendations for OCR processing.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with quality metrics and recommendations:
        {
            'blur_score': float,       # Higher is better, >100 is acceptable
            'brightness': float,       # 0-255, 100-150 is optimal
            'contrast': float,         # Standard deviation, >30 is good
            'resolution': tuple,       # (width, height)
            'is_acceptable': bool,     # Overall assessment
            'recommendations': list    # Suggestions for improvement
        }
    """
    try:
        image = load_image(image_path)

        # Convert to grayscale for analysis
        gray = to_grayscale(image)

        # 1. Blur detection using Laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = float(laplacian.var())

        # 2. Brightness analysis
        brightness = float(np.mean(gray))  # type: ignore[call-overload]

        # 3. Contrast analysis (standard deviation)
        contrast = float(gray.std())

        # 4. Resolution check
        h, w = gray.shape
        resolution = (w, h)
        resolution_ok = h >= 300 and w >= 300

        # 5. Overall assessment
        is_acceptable = (
            blur_score > 100  # Not too blurry
            and 50 < brightness < 200  # Not too dark or bright
            and contrast > 30  # Sufficient contrast
            and resolution_ok  # Minimum resolution
        )

        # 6. Generate recommendations
        recommendations = []
        if blur_score <= 100:
            recommendations.append(
                "Image is too blurry - use sharper image or stabilize camera"
            )
        if brightness <= 50:
            recommendations.append("Image too dark - increase lighting or exposure")
        elif brightness >= 200:
            recommendations.append(
                "Image overexposed - reduce brightness or use better lighting"
            )
        if contrast <= 30:
            recommendations.append("Low contrast - improve lighting conditions")
        if not resolution_ok:
            recommendations.append(
                f"Resolution too low ({w}x{h}) - use higher resolution (min 300x300)"
            )

        # Add positive feedback if acceptable
        if is_acceptable and not recommendations:
            recommendations.append("Image quality is good for OCR processing")

        return {
            "blur_score": blur_score,
            "brightness": brightness,
            "contrast": contrast,
            "resolution": resolution,
            "is_acceptable": is_acceptable,
            "recommendations": recommendations,
        }

    except Exception as e:
        return {
            "blur_score": 0,
            "brightness": 0,
            "contrast": 0,
            "resolution": (0, 0),
            "is_acceptable": False,
            "recommendations": [f"Error analyzing image: {str(e)}"],
        }


def auto_correct_image(image: np.ndarray, quality_info: dict[str, Any]) -> np.ndarray:
    """
    Applies automatic corrections based on quality assessment.

    Args:
        image: Input image as numpy array (BGR format)
        quality_info: Quality assessment dictionary from assess_image_quality

    Returns:
        Corrected image as numpy array
    """
    try:
        corrected = image.copy()

        brightness = quality_info.get("brightness", 128)
        contrast = quality_info.get("contrast", 50)
        blur_score = quality_info.get("blur_score", 200)

        # 1. Correct low brightness
        if brightness < 80:
            # Increase brightness and contrast
            corrected = cv2.convertScaleAbs(corrected, alpha=1.3, beta=35)

        # 2. Correct high brightness (overexposure)
        elif brightness > 180:
            # Decrease brightness
            corrected = cv2.convertScaleAbs(corrected, alpha=0.8, beta=-20)

        # 3. Enhance low contrast
        if contrast < 40:
            # Use CLAHE on LAB color space for better results
            lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
            lab_l, lab_a, lab_b = cv2.split(lab)

            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            lab_l = clahe.apply(lab_l)

            # Merge channels and convert back
            corrected = cv2.cvtColor(cv2.merge([lab_l, lab_a, lab_b]), cv2.COLOR_LAB2BGR)

        # 4. Apply sharpening if moderately blurry
        if 100 < blur_score < 300:
            # Unsharp mask for better sharpening
            gaussian = cv2.GaussianBlur(corrected, (0, 0), 2.0)
            corrected = cv2.addWeighted(corrected, 1.5, gaussian, -0.5, 0)

        return corrected

    except Exception as e:
        # If correction fails, return original image
        print(f"Warning: Auto-correction failed: {e}. Using original image.")
        return image


def auto_correct_image_from_path(
    image_path: str, quality_info: dict[str, Any] | None = None
) -> np.ndarray:
    """
    Load, assess, and auto-correct an image from path.

    Args:
        image_path: Path to the image file
        quality_info: Optional pre-computed quality info (if None, will assess)

    Returns:
        Auto-corrected image as numpy array
    """
    image = load_image(image_path)

    # Assess quality if not provided
    if quality_info is None:
        quality_info = assess_image_quality(image_path)

    # Apply corrections only if needed
    if not quality_info.get("is_acceptable", True):
        return auto_correct_image(image, quality_info)

    return image


def should_process_image(quality_info: dict[str, Any]) -> tuple[bool, str]:
    """
    Determines if an image should be processed based on quality assessment.

    Args:
        quality_info: Quality assessment dictionary

    Returns:
        Tuple of (should_process, reason)
    """
    # Check critical failures
    if quality_info["resolution"][0] < 100 or quality_info["resolution"][1] < 100:
        return False, "Resolution too low (minimum 100x100 pixels)"

    if quality_info["blur_score"] < 50:
        return False, "Image too blurry to process reliably"

    if quality_info["brightness"] < 20 or quality_info["brightness"] > 235:
        return False, "Image brightness out of acceptable range"

    if quality_info["contrast"] < 10:
        return False, "Insufficient contrast for text detection"

    # Image can be processed (possibly with corrections)
    return True, "Image is processable"

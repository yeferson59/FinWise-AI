"""
Image Quality Assessment and Auto-correction Module
Analyzes image quality and applies automatic corrections for better OCR results.
Enhanced with more sophisticated analysis and correction techniques.
"""

import cv2
import numpy as np
from typing import Any
from app.utils.image import load_image, to_grayscale


def assess_image_quality(image_path: str) -> dict[str, Any]:
    """
    Analyzes image quality and provides recommendations for OCR processing.
    Enhanced version with more metrics and better analysis.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with quality metrics and recommendations:
        {
            'blur_score': float,       # Higher is better, >100 is acceptable
            'brightness': float,       # 0-255, 100-150 is optimal
            'contrast': float,         # Standard deviation, >30 is good
            'resolution': tuple,       # (width, height)
            'noise_level': float,      # Estimated noise level (lower is better)
            'text_density': float,     # Estimated text content density
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

        # 2. Brightness analysis (mean intensity)
        brightness = float(np.mean(gray))

        # 3. Contrast analysis (standard deviation)
        contrast = float(gray.std())

        # 4. Resolution check
        h, w = gray.shape
        resolution = (w, h)
        resolution_ok = h >= 300 and w >= 300

        # 5. Noise level estimation using edge density
        edges = cv2.Canny(gray, 50, 150)
        _ = np.sum(edges > 0) / (h * w)  # edge_density - used for noise estimation

        # High edge density could mean noise or good text content
        # Use Sobel to differentiate
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        noise_level = float(np.std(sobel_magnitude) / np.mean(sobel_magnitude + 1))

        # 6. Text density estimation (using morphological operations)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=2)
        text_density = float(np.sum(dilated > 0) / (h * w))

        # 7. Histogram uniformity (for detecting overexposed/underexposed regions)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        _ = float(np.std(hist.flatten().tolist()))  # hist_std - uniformity metric
        hist_peak = int(np.argmax(hist))

        # 8. Overall assessment with weighted criteria
        is_acceptable = (
            blur_score > 80  # Not too blurry
            and 40 < brightness < 210  # Not too dark or bright
            and contrast > 25  # Sufficient contrast
            and resolution_ok  # Minimum resolution
            and noise_level < 2.5  # Not too noisy
        )

        # 9. Generate detailed recommendations
        recommendations = []
        if blur_score <= 80:
            severity = "severely" if blur_score < 50 else "moderately"
            recommendations.append(
                f"Image is {severity} blurry (score: {blur_score:.0f}) - use sharper image or stabilize camera"
            )
        if brightness <= 40:
            recommendations.append(
                f"Image too dark (brightness: {brightness:.0f}) - increase lighting or exposure"
            )
        elif brightness >= 210:
            recommendations.append(
                f"Image overexposed (brightness: {brightness:.0f}) - reduce brightness or use better lighting"
            )
        if contrast <= 25:
            recommendations.append(
                f"Low contrast ({contrast:.0f}) - improve lighting conditions or use flash"
            )
        if not resolution_ok:
            recommendations.append(
                f"Resolution too low ({w}x{h}) - use higher resolution (min 300x300)"
            )
        if noise_level >= 2.5:
            recommendations.append(
                f"High noise level ({noise_level:.2f}) - use better lighting or image stabilization"
            )
        if text_density < 0.01:
            recommendations.append(
                "Very low text density detected - verify document orientation"
            )
        elif text_density > 0.5:
            recommendations.append(
                "Very high ink density - document may be inverted or have dark background"
            )

        # Add positive feedback if acceptable
        if is_acceptable and not recommendations:
            recommendations.append("Image quality is good for OCR processing")

        return {
            "blur_score": blur_score,
            "brightness": brightness,
            "brightness_score": brightness,  # Alias for compatibility
            "contrast": contrast,
            "resolution": resolution,
            "noise_level": noise_level,
            "text_density": text_density,
            "histogram_peak": hist_peak,
            "is_acceptable": is_acceptable,
            "recommendations": recommendations,
            "quality_grade": _calculate_quality_grade(
                blur_score, brightness, contrast, noise_level
            ),
        }

    except Exception as e:
        return {
            "blur_score": 0,
            "brightness": 0,
            "brightness_score": 0,
            "contrast": 0,
            "resolution": (0, 0),
            "noise_level": 999,
            "text_density": 0,
            "histogram_peak": 0,
            "is_acceptable": False,
            "recommendations": [f"Error analyzing image: {str(e)}"],
            "quality_grade": "F",
        }


def _calculate_quality_grade(
    blur: float, brightness: float, contrast: float, noise: float
) -> str:
    """Calculate an overall quality grade A-F based on metrics."""
    score = 0

    # Blur score (max 30 points)
    if blur >= 200:
        score += 30
    elif blur >= 100:
        score += 20
    elif blur >= 50:
        score += 10

    # Brightness score (max 25 points)
    if 80 <= brightness <= 170:
        score += 25
    elif 50 <= brightness <= 200:
        score += 15
    elif 30 <= brightness <= 220:
        score += 5

    # Contrast score (max 25 points)
    if contrast >= 50:
        score += 25
    elif contrast >= 35:
        score += 15
    elif contrast >= 20:
        score += 5

    # Noise score (max 20 points)
    if noise < 1.0:
        score += 20
    elif noise < 1.5:
        score += 15
    elif noise < 2.0:
        score += 10
    elif noise < 2.5:
        score += 5

    # Map to grade
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def auto_correct_image(image: np.ndarray, quality_info: dict[str, Any]) -> np.ndarray:
    """
    Applies automatic corrections based on quality assessment.
    Enhanced version with more sophisticated correction techniques.

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
        noise_level = quality_info.get("noise_level", 1.0)

        # 1. Reduce noise first if present (before other corrections)
        if noise_level > 1.5:
            # Use bilateral filter for edge-preserving denoising
            corrected = cv2.bilateralFilter(corrected, 9, 75, 75)

        # 2. Correct low brightness using gamma correction
        if brightness < 70:
            # Gamma correction for dark images (gamma < 1 brightens)
            gamma = 0.6 if brightness < 40 else 0.8
            inv_gamma = 1.0 / gamma
            table = np.array(
                [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
            ).astype("uint8")
            corrected = cv2.LUT(corrected, table)

        # 3. Correct high brightness (overexposure)
        elif brightness > 190:
            # Gamma correction for bright images (gamma > 1 darkens)
            gamma = 1.3 if brightness > 220 else 1.15
            table = np.array(
                [((i / 255.0) ** gamma) * 255 for i in np.arange(0, 256)]
            ).astype("uint8")
            corrected = cv2.LUT(corrected, table)

        # 4. Enhance low contrast using adaptive histogram equalization
        if contrast < 35:
            # Convert to LAB color space for better contrast enhancement
            lab = cv2.cvtColor(corrected, cv2.COLOR_BGR2LAB)
            lab_l, lab_a, lab_b = cv2.split(lab)

            # Apply CLAHE to L channel with adaptive parameters
            clip_limit = 4.0 if contrast < 20 else 3.0
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
            lab_l = clahe.apply(lab_l)

            # Merge channels and convert back
            corrected = cv2.cvtColor(
                cv2.merge([lab_l, lab_a, lab_b]), cv2.COLOR_LAB2BGR
            )

        # 5. Apply sharpening if moderately blurry
        if blur_score < 150:
            if blur_score < 80:
                # Strong sharpening for very blurry images
                kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                corrected = cv2.filter2D(corrected, -1, kernel)
            else:
                # Unsharp mask for moderately blurry images
                gaussian = cv2.GaussianBlur(corrected, (0, 0), 3.0)
                corrected = cv2.addWeighted(corrected, 1.5, gaussian, -0.5, 0)

        # 6. Final noise reduction pass if sharpening introduced artifacts
        if blur_score < 100 and noise_level > 1.0:
            # Light bilateral filter to smooth artifacts
            corrected = cv2.bilateralFilter(corrected, 5, 50, 50)

        return corrected

    except Exception as e:
        # If correction fails, return original image
        print(f"Warning: Auto-correction failed: {e}. Using original image.")
        return image


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Apply OCR-specific enhancements to maximize text recognition accuracy.

    Args:
        image: Input image as numpy array (BGR format)

    Returns:
        Enhanced image optimized for OCR
    """
    try:
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 1. Apply bilateral filter to reduce noise while keeping edges
        denoised = cv2.bilateralFilter(gray, 11, 17, 17)

        # 2. Apply CLAHE for local contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # 3. Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # 4. Remove small noise with morphological operations
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

        return cleaned

    except Exception as e:
        print(f"Warning: OCR enhancement failed: {e}. Using original image.")
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

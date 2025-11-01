"""Common image processing utilities to reduce code duplication."""
import os
import cv2
import tempfile
import numpy as np


def load_image(filepath: str) -> np.ndarray:
    """
    Load an image from file with validation.
    
    Args:
        filepath: Path to the image file
        
    Returns:
        Image as numpy array (BGR format)
        
    Raises:
        ValueError: If file cannot be read or does not exist
    """
    image = cv2.imread(filepath)
    if image is None:
        raise ValueError(
            "Invalid image file: file exists but cannot be read as image"
            if os.path.exists(filepath)
            else "Invalid image file or file does not exist."
        )
    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale if it's not already.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def create_temp_image_file(
    suffix: str = ".png", prefix: str = "ocr_"
) -> tuple[int, str]:
    """
    Create a temporary file for image processing.
    
    Args:
        suffix: File suffix/extension (default: .png)
        prefix: File prefix (default: ocr_)
        
    Returns:
        Tuple of (file_descriptor, filepath)
    """
    return tempfile.mkstemp(suffix=suffix, prefix=prefix)


def save_temp_image(image: np.ndarray, suffix: str = ".png", prefix: str = "ocr_") -> str:
    """
    Save an image to a temporary file.
    
    Args:
        image: Image to save as numpy array
        suffix: File suffix/extension (default: .png)
        prefix: File prefix (default: ocr_)
        
    Returns:
        Path to the saved temporary file
    """
    temp_fd, temp_path = create_temp_image_file(suffix, prefix)
    os.close(temp_fd)
    cv2.imwrite(temp_path, image)
    return temp_path


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


def cleanup_temp_files(filepaths: list[str]) -> None:
    """
    Remove multiple temporary files.
    
    Args:
        filepaths: List of file paths to remove
    """
    for filepath in filepaths:
        cleanup_temp_file(filepath)


def get_image_dimensions(image: np.ndarray) -> tuple[int, int]:
    """
    Get image dimensions (width, height).
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Tuple of (width, height)
    """
    h, w = image.shape[:2]
    return w, h

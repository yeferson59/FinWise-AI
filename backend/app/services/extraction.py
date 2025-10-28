import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from typing import Any
import logging
from app.ocr_config import (
    OCRConfig,
    DocumentType,
    get_profile,
)
from app.services.tesseract_wrapper import (
    extract_text_resilient,
    extract_text_with_confidence_resilient,
)

logger = logging.getLogger(__name__)


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract text from PDF files using PyMuPDF.

    Args:
        filepath: Path to the PDF file

    Returns:
        Extracted text as string
    """
    text = ""
    try:
        pdf_document = fitz.open(filepath)
        for page in pdf_document:
            page_text = page.get_text("text")
            if isinstance(page_text, str):
                text += page_text
        pdf_document.close()
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF: {str(e)}")

    return text.strip()


def extract_text_from_image(
    filepath: str,
    config: OCRConfig | None = None,
    document_type: DocumentType | None = None,
) -> str:
    """
    Extract text from image files using Tesseract OCR with custom configuration.

    Args:
        filepath: Path to the image file
        config: Custom OCR configuration (overrides document_type)
        document_type: Type of document for optimized settings

    Returns:
        Extracted text as string
    """
    try:
        image = Image.open(filepath)
    except Exception as e:
        raise ValueError(f"Error opening image file: {str(e)}")

    # Get configuration
    if config is None:
        if document_type is not None:
            profile = get_profile(document_type)
            config = profile.ocr_config
        else:
            # Use default config
            profile = get_profile(DocumentType.GENERAL)
            config = profile.ocr_config

    # Get Tesseract configuration string
    tesseract_config = config.get_tesseract_config()
    language = config.get_language()

    # Ensure image is in a compatible mode (some formats cause Tesseract errors)
    if image.mode not in ("RGB", "L", "RGBA"):
        image = image.convert("RGB")

    # Save to temporary PNG file for resilient processing
    import tempfile
    import os

    temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
    try:
        os.close(temp_fd)
        image.save(temp_path, format="PNG")
        image.close()

        # Use resilient wrapper to protect against crashes
        extracted_text = extract_text_resilient(
            temp_path, config_str=tesseract_config, lang=language
        )

        return extracted_text if extracted_text else ""

    except Exception as e:
        logger.error(f"Error during OCR processing: {e}")
        raise ValueError(f"Error during OCR processing: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


def extract_text(
    filepath: str,
    document_type: DocumentType | None = None,
    ocr_config: OCRConfig | None = None,
) -> str:
    """
    Extract text from PDF or image files with configurable OCR settings.

    Args:
        filepath: Path to the file (PDF or image)
        document_type: Type of document (receipt, invoice, etc.)
        ocr_config: Custom OCR configuration (overrides document_type)

    Returns:
        Extracted text as string

    Raises:
        ValueError: If file cannot be processed or is invalid

    Examples:
        # Extract with default settings
        text = extract_text("document.png")

        # Extract with document type optimization
        text = extract_text("receipt.jpg", document_type=DocumentType.RECEIPT)

        # Extract with custom configuration
        custom_config = OCRConfig(psm_mode=PSMMode.SINGLE_BLOCK, oem_mode=OEMMode.NEURAL_NET)
        text = extract_text("invoice.png", ocr_config=custom_config)
    """
    if not filepath:
        raise ValueError("Filepath cannot be empty")

    # Check if it's a PDF
    if filepath.lower().endswith(".pdf"):
        return extract_text_from_pdf(filepath)

    # Check if it's an image
    elif filepath.lower().endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif")
    ):
        return extract_text_from_image(filepath, ocr_config, document_type)

    else:
        raise ValueError(f"Unsupported file format: {filepath}")


def extract_text_simple(filepath: str) -> str:
    """
    Simple text extraction with default general settings.
    This is the backward-compatible version.

    Args:
        filepath: Path to the file (PDF or image)

    Returns:
        Extracted text as string
    """
    return extract_text(filepath, document_type=DocumentType.GENERAL)


def extract_text_with_confidence(
    filepath: str,
    document_type: DocumentType | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Extract text from image and return confidence scores (resilient version).

    Args:
        filepath: Path to the image file
        document_type: Type of document for optimized settings

    Returns:
        Tuple of (extracted_text, confidence_data)
        confidence_data includes per-word confidence scores
    """
    if filepath.lower().endswith(".pdf"):
        # PDFs don't have confidence scores from PyMuPDF
        text = extract_text_from_pdf(filepath)
        return text, {"note": "PDF extraction does not provide confidence scores"}

    try:
        image = Image.open(filepath)
    except Exception as e:
        raise ValueError(f"Error opening image file: {str(e)}")

    # Get configuration
    profile = get_profile(document_type or DocumentType.GENERAL)
    config = profile.ocr_config

    tesseract_config = config.get_tesseract_config()
    language = config.get_language()

    # Ensure image is in compatible mode
    if image.mode not in ("RGB", "L", "RGBA"):
        image = image.convert("RGB")

    # Save to temporary PNG file for resilient processing
    import tempfile
    import os

    temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
    try:
        os.close(temp_fd)
        image.save(temp_path, format="PNG")
        image.close()

        # Use resilient wrapper with confidence
        text, confidence_data = extract_text_with_confidence_resilient(
            temp_path, config_str=tesseract_config, lang=language
        )

        return text if text else "", confidence_data

    except Exception as e:
        logger.error(f"Error during OCR processing with confidence: {e}")
        raise ValueError(f"Error during OCR processing with confidence: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

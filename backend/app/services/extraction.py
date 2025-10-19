import pytesseract
from PIL import Image
import fitz  # PyMuPDF


def extract_text(filepath: str) -> str:
    """
    Extract text from PDF or image files.

    Args:
        filepath: Path to the file (PDF or image)

    Returns:
        Extracted text as string
    """
    if filepath.endswith(".pdf"):
        text = ""
        pdf_document = fitz.open(filepath)
        for page in pdf_document:
            # Explicitly get text as string
            page_text = page.get_text("text")
            if isinstance(page_text, str):
                text += page_text
        pdf_document.close()
        return text
    else:
        image = Image.open(filepath)
        # image_to_string returns str by default with output_type not specified
        extracted_text = pytesseract.image_to_string(image, lang="eng")
        # Ensure we return a string
        if isinstance(extracted_text, str):
            return extracted_text
        return ""

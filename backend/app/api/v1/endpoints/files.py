from fastapi import APIRouter, UploadFile, HTTPException, Query
from app.services import storage, preprocessing, extraction
from app.ocr_config import DocumentType

router = APIRouter()


@router.post("/extract-text")
async def extract_text(
    file: UploadFile,
    document_type: str | None = Query(),
):
    """
    Extract text from uploaded file (PDF or image).

    Args:
        file: The file to extract text from
        document_type: Optional document type for optimized OCR (receipt, invoice, etc.)

    Returns:
        Dictionary with extracted text
    """
    # Validate file format
    if file.filename is not None and not file.filename.endswith(
        (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif")
    ):
        raise HTTPException(status_code=400, detail="Invalid file format")

    try:
        # Save uploaded file
        file_path = await storage.save_file(file)

        # Parse document type
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid document type. Must be one of: {', '.join([dt.value for dt in DocumentType])}",
                )

        # Only preprocess images, not PDFs
        if file_path.lower().endswith(".pdf"):
            processed_path = file_path
        else:
            processed_path = preprocessing.preprocess_image(
                file_path, document_type=doc_type
            )

        # Extract text with document type optimization
        raw_text = extraction.extract_text(processed_path, document_type=doc_type)

        return {
            "raw_text": raw_text,
            "document_type": document_type or "general",
            "file_type": "pdf" if file_path.lower().endswith(".pdf") else "image",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/extract-text-with-confidence")
async def extract_text_with_confidence(
    file: UploadFile,
    document_type: str = Query(
        description="Type of document: receipt, invoice, document, form, screenshot, photo, general"
    ),
):
    """
    Extract text from uploaded image with OCR confidence scores.
    Note: Only works with image files, not PDFs.

    Args:
        file: The image file to extract text from
        document_type: Optional document type for optimized OCR

    Returns:
        Dictionary with extracted text and confidence metrics
    """
    # Validate file format (images only)
    if file.filename is not None and not file.filename.endswith(
        (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. This endpoint only supports image files.",
        )

    try:
        # Save uploaded file
        file_path = await storage.save_file(file)

        # Parse document type
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType(document_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid document type. Must be one of: {', '.join([dt.value for dt in DocumentType])}",
                )

        # Preprocess image
        processed_path = preprocessing.preprocess_image(
            file_path, document_type=doc_type
        )

        # Extract text with confidence
        raw_text, confidence_data = extraction.extract_text_with_confidence(
            processed_path, document_type=doc_type
        )

        return {
            "raw_text": raw_text,
            "confidence": confidence_data,
            "document_type": document_type or "general",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/document-types")
async def get_document_types():
    """
    Get list of supported document types with descriptions.

    Returns:
        List of document types and their descriptions
    """
    from app.ocr_config import PROFILES

    return {
        "document_types": [
            {
                "type": doc_type.value,
                "name": profile.name,
                "description": profile.description,
            }
            for doc_type, profile in PROFILES.items()
        ]
    }

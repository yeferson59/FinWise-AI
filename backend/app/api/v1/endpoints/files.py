from typing import Annotated
from fastapi import APIRouter, UploadFile, HTTPException, Query
from app.services import storage, preprocessing, extraction
from app.services import intelligent_extraction
from app.ocr_config import DocumentType
from faster_whisper import WhisperModel

router = APIRouter()


@router.post("/extract-text")
async def extract_text(
    document_type: Annotated[str | None, Query],
    file: UploadFile,
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
    document_type: Annotated[
        str,
        Query(
            description="Type of document: receipt, invoice, document, form, screenshot, photo, general"
        ),
    ],
    file: UploadFile,
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


@router.post("/extract-text-intelligent")
async def extract_text_intelligent_endpoint(
    document_type: Annotated[
        str | None,
        Query(
            description="Type of document: receipt, invoice, document, form, screenshot, photo, general",
        ),
    ],
    language: Annotated[
        str | None,
        Query(
            description="Language code: 'eng', 'spa', or 'eng+spa' (default: auto-detect)",
        ),
    ],
    file: UploadFile,
):
    """
    Extract text using intelligent agent with fallback strategies and post-processing.
    This endpoint provides better accuracy through:
    - Multiple extraction attempts with different settings
    - Automatic language detection
    - Text cleaning and normalization
    - Quality validation

    Args:
        file: The file to extract text from (PDF or image)
        document_type: Optional document type for optimized OCR
        language: Optional language preference

    Returns:
        Dictionary with extracted text, metadata, and quality assessment
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
            # For PDFs, use standard extraction
            raw_text = extraction.extract_text(processed_path, document_type=doc_type)
            cleaned_text = intelligent_extraction.clean_text(raw_text)
            detected_lang = intelligent_extraction.detect_language(cleaned_text)

            return {
                "text": cleaned_text,
                "raw_text": raw_text,
                "metadata": {
                    "method_used": "pdf_direct",
                    "detected_language": detected_lang,
                    "text_length": len(cleaned_text),
                    "file_type": "pdf",
                },
                "document_type": document_type or "general",
                "quality": {
                    "note": "PDF extraction does not provide confidence scores"
                },
            }
        else:
            # Preprocess image
            processed_path = preprocessing.preprocess_image(
                file_path, document_type=doc_type
            )

            # Use intelligent extraction with fallback
            extracted_text, metadata = intelligent_extraction.extract_with_fallback(
                processed_path, doc_type, language
            )

            # Get confidence data for quality assessment if available
            if metadata.get("original_confidence"):
                quality = intelligent_extraction.validate_extraction_quality(
                    extracted_text, metadata["original_confidence"]
                )
            else:
                quality = {
                    "note": "Quality metrics not available for this extraction method"
                }

            return {
                "text": extracted_text,
                "metadata": metadata,
                "document_type": document_type or "general",
                "quality": quality,
                "file_type": "image",
            }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported OCR languages.

    Returns:
        List of supported language codes and names
    """
    return {
        "languages": [
            {"code": "eng", "name": "English", "description": "English language OCR"},
            {
                "code": "spa",
                "name": "Spanish",
                "description": "Spanish language OCR (Español)",
            },
            {
                "code": "eng+spa",
                "name": "English + Spanish",
                "description": "Bilingual OCR for documents with both languages",
            },
        ],
        "default": "eng+spa",
        "recommendation": "Use 'eng+spa' for best results with mixed-language documents",
    }


model_audio = WhisperModel("base", device="cpu")


@router.post("/audio/extract-text")
async def transcribe_audio(file: UploadFile):
    audio_path = await storage.save_file(file)
    segments, info = model_audio.transcribe(audio=audio_path)
    full_text = " ".join([segment.text for segment in segments])
    return {"text": full_text.strip()}

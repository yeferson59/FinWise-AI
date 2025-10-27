from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, UploadFile
from faster_whisper import WhisperModel

from app.config import get_settings
from app.ocr_config import PROFILES, DocumentType
from app.services import extraction, intelligent_extraction, preprocessing, storage

router = APIRouter()

# Supported file extensions
SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif")
SUPPORTED_FILE_EXTENSIONS = (".pdf",) + SUPPORTED_IMAGE_EXTENSIONS


def validate_file_format(filename: str | None, image_only: bool = False) -> None:
    """Validate uploaded file format.

    Args:
        filename: Name of the uploaded file
        image_only: If True, only image formats are allowed

    Raises:
        HTTPException: If file format is invalid
    """
    if filename is None:
        raise HTTPException(status_code=400, detail="Filename is required")

    allowed_extensions = (
        SUPPORTED_IMAGE_EXTENSIONS if image_only else SUPPORTED_FILE_EXTENSIONS
    )
    if not filename.lower().endswith(allowed_extensions):
        detail = (
            "Invalid file format. This endpoint only supports image files."
            if image_only
            else "Invalid file format"
        )
        raise HTTPException(status_code=400, detail=detail)


def parse_document_type(document_type: str | None) -> DocumentType | None:
    """Parse and validate document type string.

    Args:
        document_type: Document type string

    Returns:
        DocumentType enum or None

    Raises:
        HTTPException: If document type is invalid
    """
    if not document_type:
        return None

    try:
        return DocumentType(document_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join([dt.value for dt in DocumentType])}",
        )


async def upload_to_s3_if_configured(local_path: str) -> str | None:
    """Upload file to S3 if S3 storage is configured.

    Args:
        local_path: Path to local file

    Returns:
        File ID from S3 or None if not uploaded
    """
    settings = get_settings()
    if settings.file_storage_type != "s3":
        return None

    try:
        filename = Path(local_path).name
        return await storage.save_file_from_path(local_path, filename=filename)
    except Exception as e:
        print(f"Warning: Failed to upload original file to S3: {e}")
        return None


def cleanup_files(
    processed_path: str | None, local_path: str | None, is_pdf: bool
) -> None:
    """Clean up temporary files after processing.

    Args:
        processed_path: Path to preprocessed file
        local_path: Path to original local file
        is_pdf: Whether the file is a PDF
    """
    # Clean up preprocessed image (only if it's not a PDF and not the original)
    if processed_path and not is_pdf and processed_path != local_path:
        preprocessing.cleanup_temp_file(processed_path)

    # Clean up original local file (only if stored in S3, otherwise keep it in local storage)
    settings = get_settings()
    if local_path and settings.file_storage_type == "s3":
        preprocessing.cleanup_temp_file(local_path)


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
    validate_file_format(file.filename)

    processed_path = None
    local_path = None
    is_pdf = False

    try:
        local_path = await storage.save_file_locally(file)
        is_pdf = local_path.lower().endswith(".pdf")
        doc_type = parse_document_type(document_type)

        if is_pdf:
            processed_path = local_path
        else:
            processed_path = preprocessing.preprocess_image(
                local_path, document_type=doc_type, save_to_temp=True
            )

        raw_text = extraction.extract_text(processed_path, document_type=doc_type)
        original_file_id = await upload_to_s3_if_configured(local_path)

        result = {
            "raw_text": raw_text,
            "document_type": document_type or "general",
            "file_type": "pdf" if is_pdf else "image",
        }

        if original_file_id:
            result["file_id"] = original_file_id

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        cleanup_files(processed_path, local_path, is_pdf)


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
    validate_file_format(file.filename, image_only=True)

    processed_path = None
    local_path = None

    try:
        local_path = await storage.save_file_locally(file)
        doc_type = parse_document_type(document_type)

        processed_path = preprocessing.preprocess_image(
            local_path, document_type=doc_type, save_to_temp=True
        )

        raw_text, confidence_data = extraction.extract_text_with_confidence(
            processed_path, document_type=doc_type
        )

        original_file_id = await upload_to_s3_if_configured(local_path)

        result = {
            "raw_text": raw_text,
            "confidence": confidence_data,
            "document_type": document_type or "general",
        }

        if original_file_id:
            result["file_id"] = original_file_id

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        cleanup_files(processed_path, local_path, is_pdf=False)


@router.get("/document-types")
async def get_document_types():
    """Get list of supported document types with descriptions."""
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
    validate_file_format(file.filename)

    processed_path = None
    local_path = None
    is_pdf = False

    try:
        local_path = await storage.save_file_locally(file)
        is_pdf = local_path.lower().endswith(".pdf")
        doc_type = parse_document_type(document_type)

        if is_pdf:
            raw_text = extraction.extract_text(local_path, document_type=doc_type)
            cleaned_text = intelligent_extraction.clean_text(raw_text)
            detected_lang = intelligent_extraction.detect_language(cleaned_text)

            result = {
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
            processed_path = preprocessing.preprocess_image(
                local_path, document_type=doc_type, save_to_temp=True
            )

            extracted_text, metadata = intelligent_extraction.extract_with_fallback(
                processed_path, doc_type, language
            )

            if metadata.get("original_confidence"):
                quality = intelligent_extraction.validate_extraction_quality(
                    extracted_text, metadata["original_confidence"]
                )
            else:
                quality = {
                    "note": "Quality metrics not available for this extraction method"
                }

            result = {
                "text": extracted_text,
                "metadata": metadata,
                "document_type": document_type or "general",
                "quality": quality,
                "file_type": "image",
            }

        original_file_id = await upload_to_s3_if_configured(local_path)
        if original_file_id:
            result["file_id"] = original_file_id

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        cleanup_files(processed_path, local_path, is_pdf)


@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported OCR languages."""
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
    """Extract text from audio file using speech recognition."""
    file_identifier = await storage.save_file(file)
    async with storage.get_local_path(file_identifier) as local_path:
        segments, _ = model_audio.transcribe(audio=local_path)
        full_text = " ".join([segment.text for segment in segments])
    return {"text": full_text.strip()}

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, UploadFile
from faster_whisper import WhisperModel

from app.config import get_settings
from app.ocr_config import DocumentType
from app.services import extraction, intelligent_extraction, preprocessing, storage

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

    processed_path = None
    local_path = None
    is_pdf = False
    original_file_id = None

    try:
        # Step 1: Save uploaded file LOCALLY first for processing
        local_path = await storage.save_file_locally(file)

        # Step 2: Check if it's a PDF
        is_pdf = local_path.lower().endswith(".pdf")

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

        # Step 3: Only preprocess images, not PDFs
        if is_pdf:
            processed_path = local_path
        else:
            # Step 4: Preprocess image (saved to temp location)
            processed_path = preprocessing.preprocess_image(
                local_path, document_type=doc_type, save_to_temp=True
            )

        # Step 5: Extract text with document type optimization
        raw_text = extraction.extract_text(processed_path, document_type=doc_type)

        # Step 5: After successful OCR, upload original file to S3 if configured
        settings = get_settings()
        if settings.file_storage_type == "s3":
            try:
                # Generate a filename for S3
                from pathlib import Path

                original_filename = Path(local_path).name
                original_file_id = await storage.save_file_from_path(
                    local_path, filename=original_filename
                )
            except Exception as e:
                # Log but don't fail if S3 upload doesn't work
                print(f"Warning: Failed to upload original file to S3: {e}")

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
        # Step 6: Clean up temporary files
        # Clean up preprocessed image (only if it's not a PDF and not the original)
        if processed_path and not is_pdf and processed_path != local_path:
            preprocessing.cleanup_temp_file(processed_path)
        # Clean up original local file (only if stored in S3, otherwise keep it in local storage)
        settings = get_settings()
        if local_path and settings.file_storage_type == "s3":
            preprocessing.cleanup_temp_file(local_path)


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

    processed_path = None
    local_path = None
    original_file_id = None

    try:
        # Step 1: Save uploaded file LOCALLY first for processing
        local_path = await storage.save_file_locally(file)

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

        # Step 2: Preprocess image (saved to temp location)
        processed_path = preprocessing.preprocess_image(
            local_path, document_type=doc_type, save_to_temp=True
        )

        # Step 3: Extract text with confidence
        raw_text, confidence_data = extraction.extract_text_with_confidence(
            processed_path, document_type=doc_type
        )

        # Step 4: After successful OCR, upload original file to S3 if configured
        settings = get_settings()
        if settings.file_storage_type == "s3":
            try:
                # Generate a filename for S3
                from pathlib import Path

                original_filename = Path(local_path).name
                original_file_id = await storage.save_file_from_path(
                    local_path, filename=original_filename
                )
            except Exception as e:
                # Log but don't fail if S3 upload doesn't work
                print(f"Warning: Failed to upload original file to S3: {e}")

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
        # Step 6: Clean up temporary files
        # Clean up preprocessed image (only if it's not the original)
        if processed_path and processed_path != local_path:
            preprocessing.cleanup_temp_file(processed_path)
        # Clean up original local file (only if stored in S3, otherwise keep it in local storage)
        settings = get_settings()
        if local_path and settings.file_storage_type == "s3":
            preprocessing.cleanup_temp_file(local_path)


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

    processed_path = None
    local_path = None
    is_pdf = False
    original_file_id = None

    try:
        # Step 1: Save uploaded file LOCALLY first for processing
        local_path = await storage.save_file_locally(file)

        # Step 2: Check if it's a PDF
        is_pdf = local_path.lower().endswith(".pdf")

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

        # Step 3: Process based on file type
        if is_pdf:
            # For PDFs, use standard extraction
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
            # For images: preprocess → extract with intelligent fallback
            processed_path = preprocessing.preprocess_image(
                local_path, document_type=doc_type, save_to_temp=True
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

            result = {
                "text": extracted_text,
                "metadata": metadata,
                "document_type": document_type or "general",
                "quality": quality,
                "file_type": "image",
            }

        # Step 4: After successful OCR, upload original file to S3 if configured
        settings = get_settings()
        if settings.file_storage_type == "s3":
            try:
                # Generate a filename for S3
                from pathlib import Path

                original_filename = Path(local_path).name
                original_file_id = await storage.save_file_from_path(
                    local_path, filename=original_filename
                )
                result["file_id"] = original_file_id
            except Exception as e:
                # Log but don't fail if S3 upload doesn't work
                print(f"Warning: Failed to upload original file to S3: {e}")

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Step 5: Clean up temporary files
        # Clean up preprocessed image (only if it's not a PDF and not the original)
        if processed_path and not is_pdf and processed_path != local_path:
            preprocessing.cleanup_temp_file(processed_path)
        # Clean up original local file (only if stored in S3, otherwise keep it in local storage)
        settings = get_settings()
        if local_path and settings.file_storage_type == "s3":
            preprocessing.cleanup_temp_file(local_path)


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
    file_identifier = await storage.save_file(file)
    async with storage.get_local_path(file_identifier) as local_path:
        segments, _ = model_audio.transcribe(audio=local_path)
        full_text = " ".join([segment.text for segment in segments])
    return {"text": full_text.strip()}

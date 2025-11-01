import os
import tempfile
from pathlib import Path
from fastapi import HTTPException, UploadFile
from faster_whisper import WhisperModel
from app.config import get_settings
from app.ocr_config import PROFILES, DocumentType
from app.services import (
    extraction,
    preprocessing,
    storage,
    image_quality,
    intelligent_extraction,
    advanced_ocr,
    ocr_optimizations,
    ocr_corrections,
    ocr_cache,
)
from app.utils.image import cleanup_temp_file
import cv2

# Lazy load Whisper model to avoid loading it at import time
_whisper_model = None


def get_whisper_model():
    """Get or initialize the Whisper model lazily."""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel("base", device="cpu")
    assert _whisper_model is not None  # Satisfy type checker
    return _whisper_model


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
        cleanup_temp_file(processed_path)

    # Clean up original local file (only if stored in S3, otherwise keep it in local storage)
    settings = get_settings()
    if local_path and settings.file_storage_type == "s3":
        cleanup_temp_file(local_path)


async def extract_text(
    document_type: str | None,
    file: UploadFile,
):
    validate_file_format(file.filename)

    processed_path = None
    local_path = None
    is_pdf = False

    try:
        local_path = await storage.save_file_locally(file)
        is_pdf = local_path.lower().endswith(".pdf")
        doc_type = parse_document_type(document_type)

        if is_pdf:
            # PDF processing - standard extraction
            raw_text = extraction.extract_text(local_path, document_type=doc_type)

            # Phase 1: Apply post-processing corrections

            cleaned_text = ocr_corrections.post_process_ocr_text(raw_text, doc_type)

            original_file_id = await upload_to_s3_if_configured(local_path)

            result = {
                "raw_text": cleaned_text,
                "document_type": document_type or "general",
                "file_type": "pdf",
                "metadata": {
                    "method_used": "pdf_direct",
                    "post_processing_applied": True,
                },
                "improvements_applied": {
                    "phase1_post_processing": True,
                },
            }

            if original_file_id:
                result["file_id"] = original_file_id

            return result

        # Phase 1: Assess image quality
        quality_info = image_quality.assess_image_quality(local_path)

        # Determine image characteristics
        image = cv2.imread(local_path)

        height, width = image.shape[:2]  # type: ignore[union-attr]
        is_large = height > 4000 or width > 4000
        is_poor_quality = not quality_info["is_acceptable"]

        # Phase 1: Apply quality correction if needed
        correction_applied = False
        if is_poor_quality:
            corrected = image_quality.auto_correct_image(image, quality_info)  # type: ignore[arg-type]

            temp_fd, temp_corrected = tempfile.mkstemp(
                suffix=".png", prefix="corrected_"
            )

            os.close(temp_fd)
            _ = cv2.imwrite(temp_corrected, corrected)
            local_path = temp_corrected
            correction_applied = True

        # Select optimal processing strategy
        strategy_used = "standard"
        extracted_text = None
        metadata = {}

        try:
            if is_large:
                # Phase 3: Large image - use incremental processing
                print(
                    f"📏 Large image ({width}x{height}), using incremental processing..."
                )
                extracted_text, metadata = (
                    ocr_optimizations.process_large_image_incrementally(
                        filepath=local_path,
                        document_type=doc_type,
                        tile_size=2000,
                        overlap=100,
                    )
                )
                strategy_used = "phase3_incremental"

            else:
                # Try standard extraction with cache first (Phase 1)
                try:
                    processed_path = preprocessing.preprocess_image(
                        local_path, document_type=doc_type, save_to_temp=True
                    )

                    # Phase 1: Use intelligent fallback with caching
                    extracted_text, metadata = (
                        intelligent_extraction.extract_with_fallback(
                            processed_path, doc_type, language=None, use_cache=True
                        )
                    )

                    if metadata.get("cache_hit"):
                        strategy_used = "phase1_cached"
                        print("⚡ Cache hit! Ultra-fast result")
                    else:
                        strategy_used = "phase1_standard"

                    # Check if confidence is low - upgrade to advanced if needed
                    avg_conf = metadata.get("original_confidence", {}).get(
                        "average_confidence", 100
                    )
                    if avg_conf < 75 and not is_large:
                        print(
                            f"📊 Low confidence ({avg_conf:.1f}%), upgrading to advanced strategies..."
                        )
                        extracted_text, metadata = (
                            advanced_ocr.extract_with_multiple_strategies(
                                filepath=local_path,
                                document_type=doc_type,
                                max_strategies=5,
                            )
                        )
                        strategy_used = "phase2_advanced_voting"

                except Exception as e:
                    print(f"Standard extraction failed: {e}, trying advanced...")
                    # Phase 2: Fallback to advanced strategies
                    extracted_text, metadata = (
                        advanced_ocr.extract_with_multiple_strategies(
                            filepath=local_path,
                            document_type=doc_type,
                            max_strategies=5,
                        )
                    )
                    strategy_used = "phase2_advanced_fallback"

            # Phase 1: Apply post-processing corrections
            final_text = ocr_corrections.post_process_ocr_text(
                text=extracted_text, document_type=doc_type
            )

            # Upload original file if S3 configured
            original_file_id = await upload_to_s3_if_configured(local_path)

            # Build comprehensive result
            result = {
                "raw_text": final_text,
                "document_type": document_type or "general",
                "file_type": "image",
                "metadata": {  # type: ignore[dict-item]
                    **metadata,
                    "strategy_used": strategy_used,
                    "image_size": {"width": width, "height": height},
                    "quality_info": {
                        "is_acceptable": quality_info["is_acceptable"],
                        "blur_score": quality_info.get("blur_score"),
                        "brightness_score": quality_info.get("brightness_score"),
                    },
                    "corrections_applied": {
                        "quality_correction": correction_applied,
                        "post_processing": True,
                    },
                },
                "improvements_applied": {
                    "phase1_caching": True,
                    "phase1_quality_assessment": True,
                    "phase1_auto_correction": correction_applied,
                    "phase1_post_processing": True,
                    "phase2_advanced_strategies": "phase2" in strategy_used,
                    "phase3_optimization": "phase3" in strategy_used,
                },
                "performance_note": "Using ALL OCR improvements (Phases 1-3) for best results",
            }

            if original_file_id:
                result["file_id"] = original_file_id

            return result

        except Exception as inner_e:
            # Ultimate fallback - basic extraction
            print(
                f"All advanced strategies failed: {inner_e}, using basic extraction..."
            )
            processed_path = preprocessing.preprocess_image(
                local_path, document_type=doc_type, save_to_temp=True
            )
            raw_text = extraction.extract_text(processed_path, document_type=doc_type)
            final_text = ocr_corrections.post_process_ocr_text(raw_text, doc_type)

            original_file_id = await upload_to_s3_if_configured(local_path)

            result = {
                "raw_text": final_text,
                "document_type": document_type or "general",
                "file_type": "image",
                "metadata": {  # type: ignore[dict-item]
                    "method_used": "basic_fallback",
                    "note": "Advanced strategies unavailable, used basic extraction",
                },
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


async def extract_text_confidence(
    document_type: str,
    file: UploadFile,
):
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


async def get_document_types():
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


async def extract_text_intelligent_endpoint(
    document_type: str | None, language: str | None, file: UploadFile
):
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


async def get_ocr_cache_stats():
    """Get OCR cache statistics."""

    stats = ocr_cache.get_cache_stats()
    return {"cache_stats": stats, "cache_enabled": True}


async def clear_ocr_cache(
    max_age_days: int,
):
    """Clear old OCR cache entries."""

    files_removed, errors = ocr_cache.clear_cache(max_age_days)

    return {
        "files_removed": files_removed,
        "errors": errors,
        "max_age_days": max_age_days,
    }


async def assess_image_quality_endpoint(file: UploadFile):
    """
    Assess image quality for OCR processing.
    Returns quality metrics and recommendations.
    """
    validate_file_format(file.filename, image_only=True)

    local_path = None
    try:
        local_path = await storage.save_file_locally(file)

        quality_info = image_quality.assess_image_quality(local_path)
        should_process, reason = image_quality.should_process_image(quality_info)

        return {
            "quality_assessment": quality_info,
            "should_process": should_process,
            "processing_decision": reason,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error assessing image quality: {str(e)}"
        )
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.unlink(local_path)
            except Exception:
                pass


async def extract_text_advanced(
    document_type: str | None,
    file: UploadFile,
):
    validate_file_format(file.filename, image_only=True)

    local_path = None
    try:
        local_path = await storage.save_file_locally(file)
        doc_type = parse_document_type(document_type)

        # Use advanced multi-strategy extraction
        text, metadata = advanced_ocr.extract_with_multiple_strategies(
            filepath=local_path, document_type=doc_type, max_strategies=5
        )

        original_file_id = await upload_to_s3_if_configured(local_path)

        result = {
            "extracted_text": text,
            "document_type": document_type or "general",
            "extraction_metadata": metadata,
        }

        if original_file_id:
            result["file_id"] = original_file_id

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.unlink(local_path)
            except Exception:
                pass


async def extract_text_optimized(
    document_type: str | None,
    mode: str = "parallel",
    file: UploadFile | None = None,
):
    if file is None:
        raise HTTPException(status_code=400, detail="No file provided")

    validate_file_format(file.filename, image_only=True)

    local_path = None
    try:
        local_path = await storage.save_file_locally(file)
        doc_type = parse_document_type(document_type)

        # Select optimization mode
        if mode == "parallel":
            # Parallel execution of strategies
            text, metadata = await ocr_optimizations.extract_parallel_strategies(
                filepath=local_path, document_type=doc_type, max_workers=3
            )
        elif mode == "regions":
            # Region-based processing
            text, metadata = ocr_optimizations.extract_text_by_regions(
                filepath=local_path, document_type=doc_type, min_region_area=100
            )
        elif mode == "incremental":
            # Incremental tile processing
            text, metadata = ocr_optimizations.process_large_image_incrementally(
                filepath=local_path, document_type=doc_type, tile_size=2000, overlap=100
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {mode}. Must be 'parallel', 'regions', or 'incremental'",
            )

        original_file_id = await upload_to_s3_if_configured(local_path)

        result = {
            "extracted_text": text,
            "document_type": document_type or "general",
            "optimization_mode": mode,
            "optimization_metadata": metadata,
        }

        if original_file_id:
            result["file_id"] = original_file_id

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.unlink(local_path)
            except Exception:
                pass


async def transcribe_audio(file: UploadFile):
    """Extract text from audio file using speech recognition."""
    file_identifier = await storage.save_file(file)
    async with storage.get_local_path(file_identifier) as local_path:
        model = get_whisper_model()
        segments, _ = model.transcribe(audio=local_path)
        full_text = " ".join([segment.text for segment in segments])
    return {"text": full_text.strip()}

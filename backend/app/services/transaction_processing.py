"""
Unified transaction processing service.
Orchestrates the complete flow: file upload -> text extraction -> classification -> transaction creation.
"""

import os
import re
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict

from fastapi import HTTPException, UploadFile

from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.transaction import CreateTransaction
from app.services import category as category_service
from app.services import file as file_service
from app.services import transaction as transaction_service


class FileType:
    """Supported file types for transaction processing."""

    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"


def detect_file_type(filename: str, content_type: str | None = None) -> str:
    """
    Detect file type based on filename and content type.

    Args:
        filename: Name of the uploaded file
        content_type: MIME content type

    Returns:
        File type: 'image', 'document', or 'audio'

    Raises:
        HTTPException: If file type is not supported
    """
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Check by extension first
    _, ext = os.path.splitext(filename.lower())

    # Image extensions
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
    if ext in image_exts:
        return FileType.IMAGE

    # Document extensions
    doc_exts = {".pdf"}
    if ext in doc_exts:
        return FileType.DOCUMENT

    # Audio extensions
    audio_exts = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}
    if ext in audio_exts:
        return FileType.AUDIO

    # Fallback to MIME type if available
    if content_type:
        if content_type.startswith("image/"):
            return FileType.IMAGE
        elif content_type in ["application/pdf"]:
            return FileType.DOCUMENT
        elif content_type.startswith("audio/"):
            return FileType.AUDIO

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type. Supported: images ({image_exts}), PDFs, audio ({audio_exts})",
    )


async def extract_text_from_file(
    file: UploadFile, file_type: str, document_type: str = "general"
) -> Dict[str, Any]:
    """
    Extract text from uploaded file based on its type.

    Args:
        file: Uploaded file
        file_type: Detected file type ('image', 'document', 'audio')
        document_type: Type of document for OCR optimization

    Returns:
        Dict with extracted text and metadata

    Raises:
        HTTPException: If text extraction fails
    """
    try:
        if file_type in [FileType.IMAGE, FileType.DOCUMENT]:
            try:
                result = await file_service.extract_text(
                    document_type=document_type,
                    file=file,
                )
                return {
                    "text": result.get("raw_text", ""),
                    "confidence": result.get("confidence", 0),
                    "document_type": result.get("document_type", document_type),
                    "file_type": file_type,
                    "extraction_method": "intelligent_ocr",
                }
            except Exception as e:
                try:
                    result = await file_service.extract_text(document_type, file)
                    return {
                        "text": result.get("raw_text", ""),
                        "confidence": result.get("confidence", 0),
                        "document_type": result.get("document_type", document_type),
                        "file_type": file_type,
                        "extraction_method": "basic_ocr",
                        "fallback_reason": f"Intelligent OCR failed: {str(e)}",
                    }
                except Exception as fallback_e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"OCR extraction failed for {file_type}: {str(fallback_e)}. Original error: {str(e)}",
                    )

        if file_type == FileType.AUDIO:
            try:
                result = await file_service.transcribe_audio(file)
                return {
                    "text": result.get("text", ""),
                    "language": result.get("language", "unknown"),
                    "file_type": file_type,
                    "extraction_method": "transcription",
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Audio transcription failed: {str(e)}"
                )

        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {file_type}"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


async def classify_extracted_text(
    session: SessionDep, text: str, document_type: str = "general"
) -> Category:
    """
    Classify extracted text into a category.

    Args:
        session: Database session
        text: Extracted text to classify
        document_type: Type of document

    Returns:
        Category object

    Raises:
        HTTPException: If classification fails
    """
    try:
        # Create a temporary file-like object for classification

        temp_file = UploadFile(filename="temp.txt", file=BytesIO(text.encode("utf-8")))

        category = await category_service.classification(
            session, document_type, temp_file
        )
        return category

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Text classification failed: {str(e)}"
        )


def parse_transaction_data(text: str) -> Dict[str, Any]:
    """
    Parse transaction data from extracted text.
    This is a basic implementation - can be enhanced with AI parsing.

    Args:
        text: Extracted text

    Returns:
        Dict with parsed transaction data
    """
    # Basic parsing logic - extract amount, date, description
    # This can be enhanced with more sophisticated parsing

    parsed_data = {
        "description": text[:200],  # First 200 chars as description
        "amount": None,
        "date": datetime.now(timezone.utc),
    }

    # Extract amount (look for currency patterns)
    amount_patterns = [
        r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # $123.45 or 123.45
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|COP|MXN)",  # 123.45 USD
    ]

    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Take the first match and clean it
            amount_str = matches[0].replace(",", "")
            try:
                parsed_data["amount"] = float(amount_str)
                break
            except ValueError:
                continue

    # Extract date (look for date patterns)
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # DD/MM/YYYY or MM/DD/YYYY
        r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # YYYY/MM/DD
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                if len(matches[0]) == 3:
                    d1, d2, d3 = matches[0]
                    # Assume DD/MM/YYYY format for now
                    day, month, year = int(d1), int(d2), int(d3)
                    if year < 100:
                        year += 2000
                    parsed_data["date"] = datetime(
                        year, month, day, tzinfo=timezone.utc
                    )
                    break
            except (ValueError, TypeError):
                continue

    return parsed_data


async def process_transaction_from_file(
    session: SessionDep,
    file: UploadFile,
    user_id: int,
    source_id: int,
    document_type: str = "general",
) -> Dict[str, Any]:
    """
    Complete transaction processing flow from file upload.

    Args:
        session: Database session
        file: Uploaded file
        user_id: User ID for the transaction
        source_id: Source ID for the transaction
        document_type: Type of document for processing optimization

    Returns:
        Dict with complete processing results

    Raises:
        HTTPException: If any step in the process fails
    """
    try:
        # Step 1: Detect file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        file_type = detect_file_type(file.filename, getattr(file, "content_type", None))

        # Step 2: Extract text from file
        try:
            extraction_result = await extract_text_from_file(
                file, file_type, document_type
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions from extraction
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from {file_type} file: {str(e)}",
            )

        # Step 3: Classify extracted text
        try:
            category = await classify_extracted_text(
                session, extraction_result["text"], document_type
            )
        except HTTPException:
            raise  # Re-raise HTTP exceptions from classification
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to classify extracted text: {str(e)}"
            )

        # Step 4: Parse transaction data from text
        try:
            parsed_data = parse_transaction_data(extraction_result["text"])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse transaction data from text: {str(e)}",
            )

        # Step 5: Create transaction
        try:
            transaction_data = CreateTransaction(
                user_id=user_id,
                category_id=category.id,
                source_id=source_id,
                description=parsed_data.get(
                    "description", f"Transaction from {file.filename}"
                ),
                amount=parsed_data.get("amount", 0.0),
                date=parsed_data.get("date", datetime.now(timezone.utc)),
            )

            transaction = await transaction_service.create_transaction(
                session, transaction_data
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create transaction: {str(e)}"
            )

        # Return complete results
        return {
            "file_info": {
                "filename": file.filename,
                "file_type": file_type,
                "size": getattr(file, "size", None),
            },
            "extraction": extraction_result,
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
            },
            "parsed_data": parsed_data,
            "transaction": transaction,
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transaction processing: {str(e)}",
        )

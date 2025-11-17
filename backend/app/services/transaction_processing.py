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

from app.core.agent import get_agent
from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.transaction import CreateTransaction
from app.services import category as category_service
from app.services import file as file_service
from app.services import source as source_service
from app.services import transaction as transaction_service
from app.services import user as user_service


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
                parsed_data["amount"] = float(amount_str)  # type: ignore[assignment]
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


async def parse_transaction_with_ai(text: str) -> Dict[str, Any]:
    """
    Parse transaction data from extracted text using AI agent.
    This enhances the basic regex parsing with intelligent extraction.

    Args:
        text: Extracted text

    Returns:
        Dict with parsed transaction data
    """
    try:
        agent = get_agent()
        prompt = f"""Analiza el siguiente texto extraído de un documento financiero (recibo, factura, etc.) y extrae la información de transacción.

Texto:
{text}

Devuelve SOLO un objeto JSON válido con la siguiente estructura exacta:

{{
  "amount": número decimal (monto de la transacción, puede ser positivo o negativo),
  "date": "fecha en formato YYYY-MM-DD" (fecha de la transacción, si no se encuentra usa la fecha actual),
  "description": "descripción breve de la transacción (máximo 200 caracteres)",
  "confidence": número entre 0 y 100 (confianza en la extracción)
}}

Reglas:
- Si no encuentras un monto claro, usa 0.0
- Si no encuentras fecha, usa la fecha actual en formato YYYY-MM-DD
- La descripción debe ser concisa pero informativa
- Confianza: 100 si todos los datos están claros, menos si hay ambigüedades

Devuelve únicamente el JSON."""

        response = await agent.run(text, instructions=prompt)
        result = response.output

        # Try to parse as JSON
        import json

        try:
            parsed = json.loads(result)
            # Validate required fields
            if "amount" not in parsed:
                parsed["amount"] = 0.0
            if "date" not in parsed:
                parsed["date"] = datetime.now(timezone.utc).date().isoformat()
            if "description" not in parsed:
                parsed["description"] = text[:200]
            if "confidence" not in parsed:
                parsed["confidence"] = 50

            # Convert date string to datetime
            try:
                parsed["date"] = datetime.fromisoformat(parsed["date"]).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                parsed["date"] = datetime.now(timezone.utc)

            return parsed

        except json.JSONDecodeError:
            # Fallback to basic parsing if AI fails
            return parse_transaction_data(text)

    except Exception:
        # Fallback to basic parsing
        return parse_transaction_data(text)


async def process_transaction_from_file(
    session: SessionDep,
    file: UploadFile,
    user_id: int,
    source_id: int | None = None,
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
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        file_type = detect_file_type(file.filename, getattr(file, "content_type", None))
        try:
            extraction_result = await file_service.extract_text(document_type, file)
            print("=== OCR RAW EXTRACTION RESULT ===")
            print(extraction_result)
            print("=== RAW TEXT ===")
            print(extraction_result.get("raw_text", "NO TEXT"))

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from {file_type} file: {str(e)}",
            )

        text = str(extraction_result.get("raw_text", ""))

        # Validate user exists
        try:
            await user_service.get_user(user_id, session)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid user_id: {str(e)}")

        # Step 3: Classify category from text
        try:
            category = await category_service.classify_category_from_text(
                session, text, document_type
            )
        except Exception as e:
            # Fallback: use first available category
            try:
                categories = await category_service.get_all_categories(session, 0, 1)
                if categories:
                    category = categories[0]
                else:
                    raise HTTPException(
                        status_code=500, detail="No categories available for fallback"
                    )
            except Exception:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to classify category and no fallback available: {str(e)}",
                )

        # Step 4: Classify source (if not provided)
        if source_id is None:
            try:
                source = await source_service.classify_source_from_text(
                    session, text, document_type
                )
                source_id = source.id
            except Exception as e:
                # Fallback: use first available source
                try:
                    sources = await source_service.get_all_sources(session, 0, 1)
                    if sources:
                        source = sources[0]
                        source_id = source.id
                    else:
                        raise HTTPException(
                            status_code=500, detail="No sources available for fallback"
                        )
                except Exception:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to classify source and no fallback available: {str(e)}",
                    )
        else:
            # Validate provided source_id exists
            try:
                source = await source_service.get_source(session, source_id)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid source_id: {str(e)}"
                )

        assert source_id is not None  # For type checker

        # Step 5: Parse transaction data with AI
        try:
            parsed_data = await parse_transaction_with_ai(text)
            print("=== AI PARSED DATA ===")
            print(parsed_data)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse transaction data: {str(e)}",
            )

        # Step 6: Create transaction
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
            "source": {
                "id": source.id,
                "name": source.name,
                "description": getattr(source, "description", None),
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

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
    Parse transaction data from extracted text using enhanced regex patterns.
    Supports multiple currency formats and date patterns common in receipts/invoices.

    Args:
        text: Extracted text

    Returns:
        Dict with parsed transaction data (amount, date, title, description, confidence)
    """
    # Clean and prepare text
    clean_text = " ".join(text.split())  # Normalize whitespace
    
    # Try to extract merchant/store name for title
    merchant_patterns = [
        r"(?:factura|recibo|ticket)\s+(?:de\s+)?([A-Za-zÀ-ÿ\s]{3,30})",
        r"^([A-Za-zÀ-ÿ\s]{3,30})(?:\s+S\.?A\.?|\s+LLC|\s+INC)?",
        r"(?:comercio|establecimiento|tienda)\s*:?\s*([A-Za-zÀ-ÿ\s]{3,30})",
    ]
    
    merchant_name = None
    for pattern in merchant_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            merchant_name = match.group(1).strip()
            break
    
    # Generate differentiated title and description
    if merchant_name:
        title = f"Compra en {merchant_name}"[:50]
    else:
        # Use first line or first few words as title
        first_line = text.split("\n")[0].strip() if text else ""
        title = first_line[:50] if first_line else "Transacción"
    
    # Description is more detailed
    description = clean_text[:200] if clean_text else "Transacción procesada automáticamente"

    parsed_data: Dict[str, Any] = {
        "title": title,
        "description": description,
        "amount": 0.0,
        "date": datetime.now(timezone.utc),
        "confidence": 30,  # Low confidence for regex-based extraction
    }

    # Enhanced amount patterns for various formats
    amount_patterns = [
        # Total/Subtotal patterns (most reliable)
        r"(?:total|subtotal|importe|monto|valor|amount)\s*:?\s*\$?\s*([\d.,]+)",
        # Currency symbol patterns
        r"\$\s*([\d.,]+)",  # $1,234.56
        r"([\d.,]+)\s*(?:USD|EUR|COP|MXN|PEN|ARS|CLP|BRL)",  # 1234.56 USD
        r"(?:USD|EUR|COP|MXN|PEN|ARS|CLP|BRL)\s*([\d.,]+)",  # USD 1234.56
        # Generic number patterns (fallback)
        r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))",  # 1.234,56 or 1,234.56
        r"(\d+(?:[.,]\d{2}))",  # Simple decimal: 123.45 or 123,45
    ]

    amount_found = False
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for match in matches:
                # Normalize the number format
                amount_str = match.strip()
                # Handle European format (1.234,56) vs US format (1,234.56)
                if "," in amount_str and "." in amount_str:
                    # Check which is the decimal separator
                    if amount_str.rfind(",") > amount_str.rfind("."):
                        # European: 1.234,56 -> 1234.56
                        amount_str = amount_str.replace(".", "").replace(",", ".")
                    else:
                        # US: 1,234.56 -> 1234.56
                        amount_str = amount_str.replace(",", "")
                elif "," in amount_str:
                    # Could be thousands separator or decimal
                    parts = amount_str.split(",")
                    if len(parts) == 2 and len(parts[1]) == 2:
                        # Likely decimal: 123,45 -> 123.45
                        amount_str = amount_str.replace(",", ".")
                    else:
                        # Likely thousands: 1,234 -> 1234
                        amount_str = amount_str.replace(",", "")
                elif "." in amount_str:
                    # Could be thousands separator or decimal
                    parts = amount_str.split(".")
                    if len(parts) == 2 and len(parts[1]) == 2:
                        # Likely decimal: 123.45
                        pass  # Keep as is
                    elif len(parts) > 2:
                        # Multiple dots, likely thousands: 1.234.567 -> 1234567
                        amount_str = amount_str.replace(".", "")

                try:
                    amount = float(amount_str)
                    if amount > 0:
                        parsed_data["amount"] = amount
                        amount_found = True
                        break
                except ValueError:
                    continue
            if amount_found:
                break

    # Enhanced date patterns
    date_patterns = [
        # ISO format (most reliable)
        (r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", "YMD"),
        # Named months in Spanish
        (r"(\d{1,2})\s+(?:de\s+)?(?:ene(?:ro)?|feb(?:rero)?|mar(?:zo)?|abr(?:il)?|may(?:o)?|jun(?:io)?|jul(?:io)?|ago(?:sto)?|sep(?:tiembre)?|oct(?:ubre)?|nov(?:iembre)?|dic(?:iembre)?)\s+(?:de\s+)?(\d{2,4})", "DMY_NAMED"),
        # DD/MM/YYYY or DD-MM-YYYY
        (r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", "DMY"),
        # DD/MM/YY or DD-MM-YY
        (r"(\d{1,2})[-/](\d{1,2})[-/](\d{2})\b", "DMY_SHORT"),
    ]

    month_map = {
        "ene": 1, "enero": 1, "feb": 2, "febrero": 2, "mar": 3, "marzo": 3,
        "abr": 4, "abril": 4, "may": 5, "mayo": 5, "jun": 6, "junio": 6,
        "jul": 7, "julio": 7, "ago": 8, "agosto": 8, "sep": 9, "septiembre": 9,
        "oct": 10, "octubre": 10, "nov": 11, "noviembre": 11, "dic": 12, "diciembre": 12
    }

    date_found = False
    for pattern, format_type in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                match = matches[0]
                if format_type == "YMD":
                    year, month, day = int(match[0]), int(match[1]), int(match[2])
                elif format_type == "DMY":
                    day, month, year = int(match[0]), int(match[1]), int(match[2])
                elif format_type == "DMY_SHORT":
                    day, month, year = int(match[0]), int(match[1]), int(match[2])
                    year = 2000 + year if year < 100 else year
                elif format_type == "DMY_NAMED":
                    day = int(match[0])
                    month_str = match[1].lower() if len(match) > 1 else ""
                    year = int(match[2]) if len(match) > 2 else datetime.now().year
                    if year < 100:
                        year = 2000 + year
                    # Find month from text
                    for key, val in month_map.items():
                        if key in text.lower():
                            month = val
                            break
                    else:
                        continue
                else:
                    continue

                # Validate date
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    parsed_data["date"] = datetime(year, month, day, tzinfo=timezone.utc)
                    date_found = True
                    break
            except (ValueError, TypeError, IndexError):
                continue

    # Update confidence based on what was found
    if amount_found and date_found:
        parsed_data["confidence"] = 60
    elif amount_found or date_found:
        parsed_data["confidence"] = 40

    return parsed_data


async def parse_transaction_with_ai(text: str) -> Dict[str, Any]:
    """
    Parse transaction data from extracted text using AI agent.
    This enhances the basic regex parsing with intelligent extraction.

    Args:
        text: Extracted text

    Returns:
        Dict with parsed transaction data including differentiated title and description
    """
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    try:
        agent = get_agent()
        prompt = f"""Analiza el siguiente texto extraído de un documento financiero (recibo, factura, etc.) y extrae la información de transacción.

Texto:
{text}

Devuelve SOLO un objeto JSON válido con la siguiente estructura exacta:

{{
  "amount": número decimal (monto de la transacción),
  "date": "fecha en formato YYYY-MM-DD" (fecha de la transacción, si no se encuentra usa "{current_date}"),
  "title": "título corto y descriptivo (máx 50 caracteres) - ej: 'Compra en Supermercado XYZ', 'Pago Netflix'",
  "description": "descripción detallada con contexto (máx 200 caracteres) - incluye detalles adicionales",
  "confidence": número entre 0 y 100 (confianza en la extracción)
}}

REGLAS IMPORTANTES:
1. "title" debe ser CORTO (máx 50 caracteres): resume QUÉ es la transacción
2. "description" debe ser DETALLADA (máx 200 caracteres): proporciona el contexto completo
3. "title" y "description" DEBEN SER DIFERENTES
4. Si no encuentras un monto claro, usa 0.0
5. Si no encuentras fecha, usa la fecha actual
6. Devuelve únicamente el JSON."""

        response = await agent.run(text, instructions=prompt)
        result = response.output

        # Try to parse as JSON
        import json

        try:
            # Clean potential markdown code blocks
            result_clean = result.strip()
            if result_clean.startswith("```json"):
                result_clean = result_clean[7:]
            if result_clean.startswith("```"):
                result_clean = result_clean[3:]
            if result_clean.endswith("```"):
                result_clean = result_clean[:-3]
            result_clean = result_clean.strip()
            
            parsed = json.loads(result_clean)
            
            # Validate required fields
            if "amount" not in parsed:
                parsed["amount"] = 0.0
            if "date" not in parsed:
                parsed["date"] = current_date
            if "title" not in parsed or not parsed["title"]:
                parsed["title"] = text[:50] if text else "Transacción"
            if "description" not in parsed or not parsed["description"]:
                parsed["description"] = text[:200] if text else "Transacción procesada"
            if "confidence" not in parsed:
                parsed["confidence"] = 50
            
            # Ensure title and description are different
            if parsed["title"] == parsed["description"]:
                if len(parsed["description"]) > 50:
                    parsed["title"] = parsed["description"][:50]
                else:
                    parsed["description"] = f"{parsed['title']}. Monto: ${parsed['amount']:.2f}"

            # Convert date string to datetime
            try:
                if isinstance(parsed["date"], str):
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


async def unified_ai_extraction(
    text: str,
    category_names: list[str],
    source_names: list[str],
    document_type: str = "general",
) -> Dict[str, Any]:
    """
    Unified AI extraction that parses transaction data, category and source in a single call.
    This significantly reduces latency by avoiding multiple AI roundtrips.

    Args:
        text: Extracted text from OCR
        category_names: List of available category names
        source_names: List of available source names
        document_type: Type of document being processed

    Returns:
        Dict with amount, date, description, category_name, source_name, and confidence
    """
    import json

    agent = get_agent()

    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    prompt = f"""Eres un experto en análisis de documentos financieros. Analiza el siguiente texto extraído de un documento ({document_type}) y extrae TODA la información en una sola respuesta.

TEXTO EXTRAÍDO:
{text}

CATEGORÍAS DISPONIBLES:
{json.dumps(category_names, ensure_ascii=False)}

FUENTES/ORÍGENES DISPONIBLES:
{json.dumps(source_names, ensure_ascii=False)}

Devuelve SOLO un objeto JSON válido con esta estructura exacta:

{{
  "amount": número decimal (monto total de la transacción),
  "date": "YYYY-MM-DD" (fecha de la transacción, usa "{current_date}" si no se encuentra),
  "title": "título corto y descriptivo (máx 50 caracteres) - ej: 'Compra en Supermercado XYZ', 'Pago de Factura Luz', 'Retiro ATM'",
  "description": "descripción detallada de la transacción con contexto adicional (máx 200 caracteres) - incluye detalles como items comprados, número de factura, dirección, etc.",
  "category_name": "nombre exacto de la categoría más apropiada de la lista",
  "source_name": "nombre exacto de la fuente/origen más apropiado de la lista",
  "confidence": número 0-100 (confianza general de la extracción),
  "extraction_details": {{
    "amount_found": boolean (si se encontró un monto claro),
    "date_found": boolean (si se encontró una fecha),
    "merchant_name": "nombre del comercio/empresa si se detecta" o null
  }}
}}

REGLAS IMPORTANTES:
1. "title" debe ser CORTO y CONCISO (máx 50 caracteres): identifica QUÉ es la transacción
   - Ejemplos: "Compra en Amazon", "Pago Netflix", "Supermercado Éxito", "Taxi Uber"
2. "description" debe ser DETALLADA (máx 200 caracteres): proporciona el contexto completo
   - Ejemplos: "Compra de 3 productos electrónicos - Factura #12345", "Suscripción mensual de streaming - Renovación automática"
3. "title" y "description" DEBEN SER DIFERENTES - el título es un resumen, la descripción es el detalle
4. "category_name" DEBE ser exactamente uno de los nombres de la lista de categorías
5. "source_name" DEBE ser exactamente uno de los nombres de la lista de fuentes
6. Si no encuentras un monto, usa 0.0
7. Si no encuentras fecha, usa la fecha actual
8. Analiza el contexto para elegir la categoría y fuente más apropiadas
9. Devuelve SOLO el JSON, sin explicaciones adicionales"""

    try:
        response = await agent.run(text, instructions=prompt)
        result = response.output

        # Clean potential markdown code blocks
        result_clean = result.strip()
        if result_clean.startswith("```json"):
            result_clean = result_clean[7:]
        if result_clean.startswith("```"):
            result_clean = result_clean[3:]
        if result_clean.endswith("```"):
            result_clean = result_clean[:-3]
        result_clean = result_clean.strip()

        parsed = json.loads(result_clean)

        # Validate and set defaults
        if "amount" not in parsed or parsed["amount"] is None:
            parsed["amount"] = 0.0
        if "date" not in parsed or not parsed["date"]:
            parsed["date"] = current_date
        
        # Handle title - generate from merchant_name or description if not provided
        if "title" not in parsed or not parsed["title"]:
            merchant = parsed.get("extraction_details", {}).get("merchant_name")
            if merchant:
                parsed["title"] = f"Transacción en {merchant}"[:50]
            elif parsed.get("description"):
                # Take first sentence or first 50 chars
                desc = parsed["description"]
                parsed["title"] = desc.split(".")[0][:50] if "." in desc else desc[:50]
            else:
                parsed["title"] = "Transacción"
        
        # Handle description - ensure it's different from title
        if "description" not in parsed or not parsed["description"]:
            parsed["description"] = text[:200] if text else "Transacción procesada automáticamente"
        
        # If title and description are the same, enhance the description
        if parsed["title"] == parsed["description"]:
            merchant = parsed.get("extraction_details", {}).get("merchant_name", "")
            amount = parsed.get("amount", 0)
            date_str = parsed.get("date", current_date)
            if merchant:
                parsed["description"] = f"Transacción realizada en {merchant} por ${amount:.2f} el {date_str}"[:200]
            else:
                parsed["description"] = f"Transacción por ${amount:.2f} procesada el {date_str}. {text[:100]}"[:200]
        
        if "confidence" not in parsed:
            parsed["confidence"] = 50

        # Validate category_name against available categories
        if "category_name" not in parsed or parsed["category_name"] not in category_names:
            # Try case-insensitive match
            lower_categories = {c.lower(): c for c in category_names}
            candidate = parsed.get("category_name", "").lower() if parsed.get("category_name") else ""
            if candidate in lower_categories:
                parsed["category_name"] = lower_categories[candidate]
            elif category_names:
                parsed["category_name"] = category_names[0]  # Fallback to first
            else:
                parsed["category_name"] = None

        # Validate source_name against available sources
        if "source_name" not in parsed or parsed["source_name"] not in source_names:
            # Try case-insensitive match
            lower_sources = {s.lower(): s for s in source_names}
            candidate = parsed.get("source_name", "").lower() if parsed.get("source_name") else ""
            if candidate in lower_sources:
                parsed["source_name"] = lower_sources[candidate]
            elif source_names:
                parsed["source_name"] = source_names[0]  # Fallback to first
            else:
                parsed["source_name"] = None

        # Convert date string to datetime
        try:
            if isinstance(parsed["date"], str):
                parsed["date"] = datetime.fromisoformat(parsed["date"]).replace(
                    tzinfo=timezone.utc
                )
        except ValueError:
            parsed["date"] = datetime.now(timezone.utc)

        return parsed

    except json.JSONDecodeError:
        # Fallback to basic parsing + first available category/source
        basic_parsed = parse_transaction_data(text)
        basic_parsed["category_name"] = category_names[0] if category_names else None
        basic_parsed["source_name"] = source_names[0] if source_names else None
        return basic_parsed
    except Exception:
        # Ultimate fallback
        basic_parsed = parse_transaction_data(text)
        basic_parsed["category_name"] = category_names[0] if category_names else None
        basic_parsed["source_name"] = source_names[0] if source_names else None
        return basic_parsed


async def process_transaction_from_file(
    session: SessionDep,
    file: UploadFile,
    user_id: int,
    source_id: int | None = None,
    document_type: str = "general",
    use_unified_extraction: bool = True,
) -> Dict[str, Any]:
    """
    Complete transaction processing flow from file upload.

    OPTIMIZED: Uses unified AI extraction to reduce multiple AI calls to a single one,
    significantly improving response time and consistency.

    Args:
        session: Database session
        file: Uploaded file
        user_id: User ID for the transaction
        source_id: Source ID for the transaction (optional, will be classified if not provided)
        document_type: Type of document for processing optimization
        use_unified_extraction: Use optimized single-call AI extraction (default: True)

    Returns:
        Dict with complete processing results

    Raises:
        HTTPException: If any step in the process fails
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")
        file_type = detect_file_type(file.filename, getattr(file, "content_type", None))

        # Step 1: Extract text from file (OCR/transcription)
        try:
            extraction_result = await file_service.extract_text(document_type, file)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from {file_type} file: {str(e)}",
            )

        text = str(extraction_result.get("raw_text", ""))

        # Enhance extraction result with confidence if not present
        if "confidence" not in extraction_result:
            metadata = extraction_result.get("metadata", {})
            original_conf = metadata.get("original_confidence", {})
            if isinstance(original_conf, dict):
                extraction_result["confidence"] = original_conf.get("average_confidence", 80)
            else:
                extraction_result["confidence"] = 80

        # Step 2: Validate user exists
        try:
            user = await user_service.get_user(user_id, session)
            if user is None:
                raise HTTPException(status_code=400, detail=f"User with id {user_id} not found")
        except HTTPException:
            raise
        except Exception as e:
            # Check if it's a "not found" error
            error_msg = str(e).lower()
            if "no row" in error_msg or "not found" in error_msg:
                raise HTTPException(status_code=400, detail=f"User with id {user_id} not found")
            raise HTTPException(status_code=400, detail=f"Error validating user_id {user_id}: {str(e)}")

        # Step 3: Get available categories and sources for classification
        try:
            categories = await category_service.get_all_categories(session, 0, 100)
            if not categories:
                raise HTTPException(
                    status_code=500, detail="No categories available in the database"
                )
            category_names = [c.name for c in categories]
            category_map = {c.name: c for c in categories}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch categories: {str(e)}",
            )

        # Handle source - either validate provided or prepare for classification
        source = None
        source_names: list[str] = []
        source_map: dict[str, Any] = {}

        if source_id is not None:
            # Validate provided source_id exists
            try:
                source = await source_service.get_source(session, source_id)
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid source_id: {str(e)}"
                )
        else:
            # Get available sources for classification
            try:
                sources = await source_service.get_all_sources(session, 0, 100)
                if not sources:
                    raise HTTPException(
                        status_code=500, detail="No sources available in the database"
                    )
                source_names = [s.name for s in sources]
                source_map = {s.name: s for s in sources}
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch sources: {str(e)}",
                )

        # Step 4: Unified AI extraction (single call for amount, date, description, category, source)
        if use_unified_extraction and (source_id is None or True):
            try:
                parsed_data = await unified_ai_extraction(
                    text=text,
                    category_names=category_names,
                    source_names=source_names if source_id is None else [],
                    document_type=document_type,
                )

                # Resolve category from AI result
                category_name = parsed_data.get("category_name")
                if category_name and category_name in category_map:
                    category = category_map[category_name]
                else:
                    category = categories[0]  # Fallback

                # Resolve source from AI result (if not provided)
                if source_id is None:
                    source_name = parsed_data.get("source_name")
                    if source_name and source_name in source_map:
                        source = source_map[source_name]
                        source_id = source.id
                    elif source_map:
                        source = list(source_map.values())[0]  # Fallback
                        source_id = source.id

            except Exception as e:
                # Fallback to legacy method if unified extraction fails
                parsed_data = await parse_transaction_with_ai(text)
                category = categories[0]
                if source_id is None and source_map:
                    source = list(source_map.values())[0]
                    source_id = source.id
        else:
            # Legacy sequential processing (kept for backwards compatibility)
            try:
                category = await category_service.classify_category_from_text(
                    session, text, document_type
                )
            except Exception:
                category = categories[0]

            if source_id is None:
                try:
                    source = await source_service.classify_source_from_text(
                        session, text, document_type
                    )
                    source_id = source.id
                except Exception:
                    if source_map:
                        source = list(source_map.values())[0]
                        source_id = source.id

            parsed_data = await parse_transaction_with_ai(text)

        assert source_id is not None  # For type checker
        assert source is not None

        # Step 5: Create transaction
        try:
            # Get title and description from parsed data
            title = parsed_data.get("title", "")
            description = parsed_data.get("description", "")
            
            # Generate title if not provided
            if not title:
                merchant = parsed_data.get("extraction_details", {}).get("merchant_name") if isinstance(parsed_data.get("extraction_details"), dict) else None
                if merchant:
                    title = f"Compra en {merchant}"[:50]
                elif description:
                    # Use first sentence or first 50 chars
                    title = description.split(".")[0][:50] if "." in description else description[:50]
                else:
                    title = f"Transacción - {file.filename}"[:50]
            
            # Generate description if not provided
            if not description:
                description = f"Transacción procesada desde archivo: {file.filename}"
            
            # Ensure title and description are different
            if title == description:
                amount = parsed_data.get("amount", 0.0)
                date_val = parsed_data.get("date", datetime.now(timezone.utc))
                date_str = date_val.strftime("%d/%m/%Y") if isinstance(date_val, datetime) else str(date_val)
                description = f"{title}. Monto: ${amount:.2f} - Fecha: {date_str}"[:200]

            transaction_data = CreateTransaction(
                user_id=user_id,
                category_id=category.id,
                source_id=source_id,
                title=title[:150],  # Ensure max length
                description=description[:300],  # Ensure max length
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

        # Return complete results with extraction details
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
            "processing_info": {
                "unified_extraction_used": use_unified_extraction,
                "ai_confidence": parsed_data.get("confidence", 0),
                "extraction_details": parsed_data.get("extraction_details", {}),
            },
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transaction processing: {str(e)}",
        )

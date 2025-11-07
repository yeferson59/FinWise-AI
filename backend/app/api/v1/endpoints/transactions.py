from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, UploadFile

from app.db.session import SessionDep
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.transaction import (
    CreateTransaction,
    TransactionFilters,
    UpdateTransaction,
)
from app.services import category as category_service
from app.services import file as file_service
from app.services import transaction
from app.utils import db

router = APIRouter()


@router.get("")
async def get_transactions(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    user_id: Annotated[int | None, Query(ge=1)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    source_id: Annotated[int | None, Query(ge=1)] = None,
    state: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    min_amount: Annotated[float | None, Query(ge=0)] = None,
    max_amount: Annotated[float | None, Query(ge=0)] = None,
    sort_by: Annotated[
        str | None, Query(pattern="^(date|amount|created_at|updated_at)$")
    ] = "date",
    sort_desc: Annotated[bool, Query()] = True,
) -> list[Transaction]:
    """Get all transactions with advanced filtering and pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        user_id: Filter by user ID (optional)
        category_id: Filter by category ID (optional)
        source_id: Filter by source ID (optional)
        state: Filter by transaction state (optional)
        start_date: Filter by start date - inclusive (optional)
        end_date: Filter by end date - inclusive (optional)
        min_amount: Filter by minimum amount (optional)
        max_amount: Filter by maximum amount (optional)
        sort_by: Field to sort by (date, amount, created_at, updated_at) (default: date)
        sort_desc: Sort in descending order (default: True)

    Returns:
        List of Transaction objects matching the filters

    Examples:
        - Get all transactions for user 1: ?user_id=1
        - Get transactions in a date range: ?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
        - Get transactions by amount range: ?min_amount=100&max_amount=500
        - Get completed transactions: ?state=completed
        - Combine filters: ?user_id=1&category_id=5&state=completed&sort_by=amount&sort_desc=false
    """
    filters = TransactionFilters(
        user_id=user_id,
        category_id=category_id,
        source_id=source_id,
        state=state,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return await transaction.get_all_transactions(session, offset, limit, filters)


@router.post("")
async def create_transaction(
    session: SessionDep,
    create_transaction: CreateTransaction,
) -> Transaction:
    return await transaction.create_transaction(session, create_transaction)


@router.get("/{transaction_id}")
async def get_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
) -> Transaction:
    return await transaction.get_transaction(session, transaction_id)


@router.put("/{transaction_id}")
async def update_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
    update_transaction: UpdateTransaction,
) -> Transaction:
    return await transaction.update_transaction(
        session, transaction_id, update_transaction
    )


@router.delete("/{transaction_id}")
async def delete_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
) -> Transaction:
    return await transaction.delete_transaction(session, transaction_id)


# Module-level cache for category lookups to avoid repeated database queries
_category_cache: dict[str, Category | None] = {}


async def classify_text_simple(session: SessionDep, text: str) -> Category:
    """
    Simple text classification based on keywords.
    Returns the first matching category or a default one.

    Performance Optimization: Uses in-memory cache for category lookups.
    """
    # Convert text to lowercase for matching
    text_lower = text.lower()

    # Define keyword mappings for common categories
    keyword_mappings = {
        "salary": ["salary", "payroll", "wage", "income", "paycheck"],
        "groceries": ["grocery", "supermarket", "food", "market", "store"],
        "rent": ["rent", "lease", "housing", "apartment"],
        "utilities": ["electricity", "water", "gas", "utility", "power"],
        "transportation": [
            "taxi",
            "uber",
            "bus",
            "train",
            "transport",
            "fuel",
            "gasoline",
        ],
        "dining out": ["restaurant", "cafe", "dinner", "lunch", "eat out"],
        "healthcare": ["doctor", "hospital", "medical", "pharmacy", "health"],
        "entertainment": ["movie", "cinema", "concert", "theater", "entertainment"],
        "shopping": ["shopping", "mall", "store", "purchase", "buy"],
        "phone": ["phone", "mobile", "cell", "telecom", "internet"],
        "insurance": ["insurance", "policy", "coverage"],
        "education": ["school", "university", "tuition", "education", "course"],
    }

    # Try to find a matching category
    for category_name, keywords in keyword_mappings.items():
        if any(keyword in text_lower for keyword in keywords):
            # Check cache first
            cache_key = category_name.title()
            if cache_key in _category_cache:
                cached_category = _category_cache[cache_key]
                if cached_category:
                    return cached_category

            # Try to find the category in the database
            category = db.get_entity_by_field(Category, "name", cache_key, session)
            if category:
                _category_cache[cache_key] = category
                return category
            else:
                _category_cache[cache_key] = None

    # If no match found, return a default category
    if "Miscellaneous" in _category_cache:
        default_category = _category_cache["Miscellaneous"]
        if default_category:
            return default_category
    else:
        default_category = db.get_entity_by_field(
            Category, "name", "Miscellaneous", session
        )
        if default_category:
            _category_cache["Miscellaneous"] = default_category
            return default_category
        _category_cache["Miscellaneous"] = None

    # If even Miscellaneous doesn't exist, get the first available category
    categories = db.get_db_entities(Category, offset=0, limit=1, session=session)
    if categories:
        return categories[0]

    # This should never happen if categories are properly initialized
    raise ValueError("No categories available in the database")


@router.post("/process-from-file")
async def process_transaction_from_file_endpoint(
    session: SessionDep,
    file: UploadFile,
    user_id: Annotated[int, Query(ge=1, description="User ID for the transaction")],
    source_id: Annotated[int, Query(ge=1, description="Source ID for the transaction")],
    document_type: Annotated[
        str,
        Query(
            description="Type of document: receipt, invoice, document, form, screenshot, photo, general",
            pattern="^(receipt|invoice|document|form|screenshot|photo|general)$",
        ),
    ] = "general",
):
    """
    Process a complete transaction from an uploaded file.

    This endpoint handles the entire flow:
    1. File upload and storage
    2. Text extraction (OCR for images/docs, transcription for audio)
    3. Automatic classification and categorization
    4. Transaction creation with parsed data

    Supported file types:
    - Images: JPG, PNG, GIF, BMP, TIFF, WebP
    - Documents: PDF
    - Audio: MP3, WAV, FLAC, M4A, AAC, OGG

    Args:
        session: Database session
        file: The file to process (image, document, or audio)
        user_id: User ID for the transaction
        source_id: Source ID for the transaction
        document_type: Type of document for optimized processing

    Returns:
        Dictionary with complete processing results including:
        - file_info: Original file information
        - extraction: Extracted text and metadata
        - category: Classified category information
        - parsed_data: Parsed transaction data
        - transaction: Created transaction object

    Raises:
        HTTPException: If processing fails at any step
    """
    # Inline implementation to avoid import issues
    try:
        # Step 1: Detect file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a filename")

        # Detect file type based on extension
        import os

        _, ext = os.path.splitext(file.filename.lower())
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"]:
            file_type = "image"
        elif ext == ".pdf":
            file_type = "document"
        elif ext in [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"]:
            file_type = "audio"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        # Step 2: Extract text from file
        extraction_result = None
        try:
            if file_type in ["image", "document"]:
                # Use intelligent OCR extraction
                ocr_result = await file_service.extract_text(
                    document_type=document_type,
                    file=file,
                )
                extraction_result = {
                    "text": ocr_result.get("raw_text", ""),
                    "confidence": ocr_result.get("confidence", 0),
                    "document_type": ocr_result.get("document_type", document_type),
                    "file_type": file_type,
                    "extraction_method": "intelligent_ocr",
                }
            elif file_type == "audio":
                # Use speech-to-text
                audio_result = await file_service.transcribe_audio(file)
                extraction_result = {
                    "text": audio_result.get("text", ""),
                    "language": audio_result.get("language", "unknown"),
                    "file_type": file_type,
                    "extraction_method": "transcription",
                }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to extract text from {file_type} file: {str(e)}",
            )

        if not extraction_result:
            raise HTTPException(
                status_code=500, detail="Text extraction failed: no result returned"
            )

        # Step 3: Classify extracted text
        try:
            category = await category_service.classify_text(
                session,
                text=str(extraction_result["text"]),
                document_type=document_type,
            )

            print(category)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to classify extracted text: {str(e)}"
            )

        # Step 4: Parse transaction data from text
        try:
            # Basic parsing logic
            import re

            text = extraction_result["text"]
            parsed_data = {
                "description": text[:200],  # First 200 chars as description
                "amount": None,
                "date": datetime.now(timezone.utc),
            }

            # Extract amount
            amount_patterns = [
                r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|EUR|COP|MXN)",
            ]
            for pattern in amount_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    amount_str = matches[0].replace(",", "")
                    try:
                        parsed_data["amount"] = float(amount_str)
                        break
                    except ValueError:
                        continue

            # Extract date
            date_patterns = [
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
                r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",
            ]
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    try:
                        if len(matches[0]) == 3:
                            d1, d2, d3 = matches[0]
                            day, month, year = int(d1), int(d2), int(d3)
                            if year < 100:
                                year += 2000
                            parsed_data["date"] = datetime(
                                year, month, day, tzinfo=timezone.utc
                            )
                            break
                    except (ValueError, TypeError):
                        continue

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

            transaction_obj = await transaction.create_transaction(
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
            "transaction": transaction_obj,
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during transaction processing: {str(e)}",
        )

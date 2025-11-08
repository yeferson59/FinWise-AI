from typing import Annotated

from fastapi import APIRouter, Path, UploadFile

from app.api.deps import PaginationParams
from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory
from app.services import category

router = APIRouter()


@router.get("")
async def get_categories(
    session: SessionDep,
    pagination: PaginationParams,
) -> list[Category]:
    """Get all categories with pagination support.

    Args:
        session: Database session
        pagination: Pagination parameters (offset, limit)

    Returns:
        List of Category objects
    """
    return await category.get_all_categories(
        session, pagination["offset"], pagination["limit"]
    )


@router.post("")
async def create_category(
    session: SessionDep, create_category: CreateCategory
) -> Category:
    return await category.create_category(session, create_category)


@router.get("/{category_id}")
async def get_category(
    session: SessionDep, category_id: Annotated[int, Path]
) -> Category:
    return await category.get_category(session, category_id)


@router.patch("/{category_id}")
async def update_category(
    session: SessionDep,
    category_id: Annotated[int, Path],
    update_category: UpdateCategory,
) -> Category:
    return await category.update_category(session, category_id, update_category)


@router.delete("/{category_id}")
async def delete_category(
    session: SessionDep, category_id: Annotated[int, Path]
) -> Category:
    return await category.delete_category(session, category_id)


@router.post("/classify")
async def classify_document(
    session: SessionDep,
    document_type: str,
    file: UploadFile,
) -> Category:
    """Classify a document or image into an existing category using AI.

    This endpoint extracts text from the uploaded file and uses an AI agent
    to classify it into one of the existing categories in the database.

    Args:
        session: Database session
        document_type: Type of document (e.g., "receipt", "invoice", "general")
        file: Uploaded file (image or PDF)

    Returns:
        Category: The matching category object

    Raises:
        HTTPException: If no categories exist, classification fails, or category not found
    """
    return await category.classification(session, document_type, file)

from app.db.session import SessionDep
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory
from app.utils.crud import CRUDService

# Initialize CRUD service for Category
_category_crud = CRUDService[Category, CreateCategory, UpdateCategory](Category)


async def get_all_categories(session: SessionDep, offset: int = 0, limit: int = 100):
    """Get all categories with pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of Category objects
    """
    return await _category_crud.get_all(session, offset, limit)


async def create_category(session: SessionDep, create_category: CreateCategory):
    return await _category_crud.create(session, create_category)


async def get_category(session: SessionDep, id: int):
    return await _category_crud.get_by_id(session, id)


async def update_category(
    session: SessionDep, id: int, update_category: UpdateCategory
):
    return await _category_crud.update(session, id, update_category)


async def delete_category(session: SessionDep, id: int):
    return await _category_crud.delete(session, id)

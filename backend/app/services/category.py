from app.db.session import SessionDep
from app.utils import db
from app.models.category import Category
from app.schemas.category import CreateCategory, UpdateCategory


async def get_all_categories(session: SessionDep, offset: int = 0, limit: int = 100):
    """Get all categories with pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of Category objects
    """
    return db.get_db_entities(Category, offset, limit, session)


async def create_category(session: SessionDep, create_category: CreateCategory):
    category = Category(**create_category.model_dump())
    db.create_db_entity(category, session)
    return category


async def get_category(session: SessionDep, id: int):
    return db.get_entity_by_id(Category, id, session)


async def update_category(
    session: SessionDep, id: int, update_category: UpdateCategory
):
    update_data = update_category.model_dump(exclude_unset=True)
    return db.update_db_entity(Category, id, update_data, session)


async def delete_category(session: SessionDep, id: int):
    category = db.get_entity_by_id(Category, id, session)
    db.delete_db_entity(Category, id, session)
    return category

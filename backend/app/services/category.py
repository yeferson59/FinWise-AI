from app.db.session import SessionDep
from app.utils import db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


async def get_all_categories(session: SessionDep):
    return db.get_db_entities(Category, 0, 10, session)


async def create_category(session: SessionDep, category_create: CategoryCreate):
    category = Category(**category_create.model_dump())
    db.create_db_entity(category, session)
    return category


async def get_category(session: SessionDep, id: int):
    return db.get_entity_by_id(Category, id, session)


async def update_category(
    session: SessionDep, id: int, category_update: CategoryUpdate
):
    update_data = category_update.model_dump(exclude_unset=True)
    return db.update_db_entity(Category, id, update_data, session)


async def delete_category(session: SessionDep, id: int):
    category = db.get_entity_by_id(Category, id, session)
    db.delete_db_entity(Category, id, session)
    return category

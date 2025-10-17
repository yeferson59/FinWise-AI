from app.models.category import Category
from app.services import category
from app.db.session import SessionDep
from fastapi import APIRouter
from app.schemas.category import CategoryCreate, CategoryUpdate

router = APIRouter()


@router.get("")
async def get_categories(session: SessionDep) -> list[Category]:
    return await category.get_all_categories(session)


@router.post("")
async def create_category(
    session: SessionDep, category_create: CategoryCreate
) -> Category:
    return await category.create_category(session, category_create)


@router.get("/{id}")
async def get_category(session: SessionDep, id: int) -> Category:
    return await category.get_category(session, id)


@router.patch("/{id}")
async def update_category(
    session: SessionDep, id: int, category_update: CategoryUpdate
) -> Category:
    return await category.update_category(session, id, category_update)


@router.delete("/{id}")
async def delete_category(session: SessionDep, id: int) -> Category:
    return await category.delete_category(session, id)

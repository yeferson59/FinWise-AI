from typing import Annotated
from app.models.category import Category
from app.services import category
from app.db.session import SessionDep
from fastapi import APIRouter, Path
from app.schemas.category import CreateCategory, UpdateCategory

router = APIRouter()


@router.get("")
async def get_categories(session: SessionDep) -> list[Category]:
    return await category.get_all_categories(session)


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

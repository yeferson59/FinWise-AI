from typing import Annotated
from app.models.category import Category
from app.services import category
from app.db.session import SessionDep
from fastapi import APIRouter, Query
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


@router.get("/{id}")
async def get_category(session: SessionDep, id: int) -> Category:
    return await category.get_category(session, id)


@router.patch("/{id}")
async def update_category(
    session: SessionDep, id: Annotated[int, Query], update_category: UpdateCategory
) -> Category:
    return await category.update_category(session, id, update_category)


@router.delete("/{id}")
async def delete_category(session: SessionDep, id: Annotated[int, Query]) -> Category:
    return await category.delete_category(session, id)

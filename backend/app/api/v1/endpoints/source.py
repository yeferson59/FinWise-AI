from typing import Annotated
from app.models.transaction import Source
from app.services import source
from app.db.session import SessionDep
from app.api.deps import PaginationParams
from fastapi import APIRouter, Path
from app.schemas.transaction import CreateSource, UpdateSource

router = APIRouter()


@router.get("")
async def get_sources(
    session: SessionDep,
    pagination: PaginationParams,
) -> list[Source]:
    """Get all sources with pagination support.

    Args:
        session: Database session
        pagination: Pagination parameters (offset, limit)

    Returns:
        List of Source objects
    """
    return await source.get_all_sources(
        session, pagination["offset"], pagination["limit"]
    )


@router.post("")
async def create_source(session: SessionDep, create_source: CreateSource) -> Source:
    return await source.create_source(session, create_source)


@router.get("/{source_id}")
async def get_source(session: SessionDep, source_id: Annotated[int, Path]) -> Source:
    return await source.get_source(session, source_id)


@router.patch("/{source_id}")
async def update_source(
    session: SessionDep,
    source_id: Annotated[int, Path],
    update_source: UpdateSource,
) -> Source:
    return await source.update_source(session, source_id, update_source)


@router.delete("/{source_id}")
async def delete_source(session: SessionDep, source_id: Annotated[int, Path]) -> Source:
    return await source.delete_source(session, source_id)

from app.db.session import SessionDep
from app.models.transaction import Source
from app.schemas.transaction import CreateSource, UpdateSource
from app.utils.crud import CRUDService

# Initialize CRUD service for Source
_source_crud = CRUDService[Source, CreateSource, UpdateSource](Source)


async def get_all_sources(session: SessionDep, offset: int = 0, limit: int = 100):
    """Get all sources with pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)

    Returns:
        List of Source objects
    """
    return await _source_crud.get_all(session, offset, limit)


async def create_source(session: SessionDep, create_source: CreateSource):
    return await _source_crud.create(session, create_source)


async def get_source(session: SessionDep, id: int):
    return await _source_crud.get_by_id(session, id)


async def update_source(
    session: SessionDep, id: int, update_source: UpdateSource
):
    return await _source_crud.update(session, id, update_source)


async def delete_source(session: SessionDep, id: int):
    return await _source_crud.delete(session, id)
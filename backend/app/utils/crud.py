"""Generic CRUD utilities for services layer."""

from typing import TypeVar, Generic
from uuid import UUID
from pydantic import BaseModel
from app.db.session import SessionDep
from app.models.base import Base, BaseUuid
from app.utils import db

T = TypeVar("T", bound=Base | BaseUuid)
CreateSchema = TypeVar("CreateSchema", bound=BaseModel)
UpdateSchema = TypeVar("UpdateSchema", bound=BaseModel)


class CRUDService(Generic[T, CreateSchema, UpdateSchema]):
    """Generic CRUD service for common database operations."""

    def __init__(self, model: type[T]):
        self.model = model

    async def create(self, session: SessionDep, create_data: CreateSchema) -> T:
        """Create a new entity."""
        entity = self.model(**create_data.model_dump())
        db.create_db_entity(entity, session)
        return entity

    async def get_by_id(self, session: SessionDep, entity_id: int | str | UUID) -> T:
        """Get entity by ID. Supports both int and UUID."""
        return db.get_entity_by_id(self.model, entity_id, session)

    async def update(
        self,
        session: SessionDep,
        entity_id: int | str | UUID,
        update_data: UpdateSchema,
    ) -> T:
        """Update an entity. Supports both int and UUID."""
        update_dict = update_data.model_dump(exclude_unset=True)
        return db.update_db_entity(self.model, entity_id, update_dict, session)

    async def delete(self, session: SessionDep, entity_id: int | str | UUID) -> T:
        """Delete an entity. Supports both int and UUID."""
        entity = db.get_entity_by_id(self.model, entity_id, session)
        db.delete_db_entity(self.model, entity_id, session)
        return entity

    async def get_all(
        self, session: SessionDep, offset: int = 0, limit: int = 100
    ) -> list[T]:
        """Get all entities with pagination."""
        return db.get_db_entities(self.model, offset, limit, session)

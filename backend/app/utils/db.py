from typing import TypeVar, cast
from app.db.session import SessionDep
from app.models.base import Base, BaseUuid
from sqlmodel import select

T = TypeVar("T", bound=Base | BaseUuid)


def create_db_entity(entity: Base | BaseUuid, session: SessionDep):
    session.add(entity)
    session.commit()
    session.refresh(entity)


def get_db_entities(
    entity: type[T], offset: int, limit: int, session: SessionDep
) -> list[T]:
    entities = session.exec(select(entity).offset(offset).limit(limit)).all()
    return cast(list[T], entities)


def get_entity_by_id(
    type_entity: type[T],
    search_field: int | str,
    session: SessionDep,
) -> T:
    result = session.exec(
        select(type_entity).where(type_entity.id == search_field)
    ).one()
    return result

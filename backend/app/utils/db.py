from typing import TypeVar, cast, Generic
from app.db.session import SessionDep
from app.models.base import Base, BaseUuid
from sqlmodel import select, func, col
from pydantic import BaseModel
import math

T = TypeVar("T", bound=Base | BaseUuid)


class PaginationMetadata(BaseModel):
    """Metadata de paginación"""

    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta genérica con paginación"""

    data: list[T]
    pagination: PaginationMetadata


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


def update_db_entity(
    type_entity: type[T],
    entity_id: int | str,
    update_data: dict[str, str | int | float | bool],
    session: SessionDep,
) -> T:
    entity = session.get(type_entity, entity_id)
    if entity is None:
        raise ValueError(f"Entity {type_entity.__name__} with id {entity_id} not found")
    for key, value in update_data.items():
        setattr(entity, key, value)
    session.commit()
    session.refresh(entity)
    return entity


def delete_db_entity(type_entity: type[T], entity_id: int | str, session: SessionDep):
    entity = session.get(type_entity, entity_id)
    if entity is not None:
        session.delete(entity)
        session.commit()


def get_entity_by_field(
    type_entity: type[T],
    field_name: str,
    field_value: str | int | float | bool,
    session: SessionDep,
) -> T | None:
    """
    Search for an entity by a specific field.

    Args:
        type_entity: Type of entity to search for
        field_name: Name of the field to search by
        field_value: Value of the field to search for
        session: Database session

    Returns:
        The found entity or None if it does not exist

    Example:
        user = get_entity_by_field(User, "email", "user@example.com", session)
    """
    field = getattr(type_entity, field_name)
    result = session.exec(select(type_entity).where(field == field_value)).first()
    return result


def get_entities_by_field(
    type_entity: type[T],
    field_name: str,
    field_value: str | int | float | bool,
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
) -> list[T]:
    """
    Search for multiple entities by a specific field with pagination.

    Args:
        type_entity: Type of entity to search for
        field_name: Name of the field to filter by
        field_value: Value of the field to search for
        session: Database session
        offset: Offset for pagination
        limit: Maximum number of results to return

    Returns:
        List of entities found

    Example:
        users = get_entities_by_field(User, "is_active", True, session, offset=0, limit=10)
    """
    field = getattr(type_entity, field_name)
    entities = session.exec(
        select(type_entity).where(field == field_value).offset(offset).limit(limit)
    ).all()
    return cast(list[T], entities)


def get_total_count(type_entity: type[T], session: SessionDep) -> int:
    """
    Gets the total count of entities.

    Args:
        type_entity: Type of entity to count
        session: Database session

    Returns:
        Total number of entities

    Example:
        total_users = get_total_count(User, session)
    """
    total = session.exec(select(func.count()).select_from(type_entity)).one()
    return total


def get_entities_with_pagination(
    type_entity: type[T],
    session: SessionDep,
    page: int = 1,
    limit: int = 10,
    order_by: str | None = None,
    order_desc: bool = False,
) -> PaginatedResponse[T]:
    """
    Retrieves entities with full pagination metadata.

    Args:
        type_entity: Type of entity to query
        session: Database session
        page: Page number (starts at 1)
        limit: Number of results per page
        order_by: Field to order by (optional)
        order_desc: If True, sort in descending order

    Returns:
        PaginatedResponse with data and pagination metadata

    Example:
        response = get_entities_with_pagination(User, session, page=1, limit=10, order_by="created_at", order_desc=True)
    """
    offset = (page - 1) * limit
    total = get_total_count(type_entity, session)

    query = select(type_entity)

    if order_by:
        order_field = getattr(type_entity, order_by)
        if order_desc:
            query = query.order_by(col(order_field).desc())
        else:
            query = query.order_by(order_field)

    entities = session.exec(query.offset(offset).limit(limit)).all()

    # Calcular metadata
    total_pages = math.ceil(total / limit) if total > 0 else 0

    pagination = PaginationMetadata(
        page=page,
        limit=limit,
        total=total,
        pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    return PaginatedResponse(data=list(entities), pagination=pagination)


def entity_exists(
    type_entity: type[T],
    field_name: str,
    field_value: str | bool | int | float,
    session: SessionDep,
) -> bool:
    """
    Checks if an entity exists with a specific value in a field.

    Args:
        type_entity: Type of entity to check
        field_name: Name of the field to check
        field_value: Value to search for in the field
        session: Database session

    Returns:
        True if it exists, False otherwise

    Example:
        exists = entity_exists(User, "email", "user@example.com", session)
    """
    field = getattr(type_entity, field_name)
    result = session.exec(
        select(func.count()).select_from(type_entity).where(field == field_value)
    ).one()
    return result > 0


def entity_exists_by_id(
    type_entity: type[T],
    entity_id: int | str,
    session: SessionDep,
) -> bool:
    """
    Checks if an entity exists by its ID.

    Args:
        type_entity: Type of entity to check
        entity_id: ID of the entity
        session: Database session

    Returns:
        True if it exists, False otherwise

    Example:
        exists = entity_exists_by_id(User, 123, session)
    """
    entity = session.get(type_entity, entity_id)
    return entity is not None


def bulk_create_entities(
    entities: list[Base | BaseUuid],
    session: SessionDep,
    refresh: bool = True,
) -> list[Base | BaseUuid]:
    """
    Create multiple entities in a single transaction.

    Performance Optimization: Optional refresh to avoid N individual database queries.

    Args:
        entities: List of entities to create
        session: Database session
        refresh: Whether to refresh entities after commit (default: True).
                Set to False for better performance if you don't need the refreshed data.

    Returns:
        List of created entities

    Example:
        users = [User(name="User1"), User(name="User2")]
        created = bulk_create_entities(users, session)
        # Or for better performance when refresh not needed:
        created = bulk_create_entities(users, session, refresh=False)
    """
    session.add_all(entities)
    session.commit()
    if refresh:
        for entity in entities:
            session.refresh(entity)
    return entities

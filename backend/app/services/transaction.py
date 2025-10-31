from app.db.session import SessionDep
from app.utils import db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    CreateTransaction,
    UpdateTransaction,
    TransactionFilters,
)
from app.utils.crud import CRUDService
from sqlmodel import select, col
from typing import cast

# Initialize CRUD service for Transaction
_transaction_crud = CRUDService[Transaction, CreateTransaction, UpdateTransaction](
    Transaction
)


async def get_all_transactions(
    session: SessionDep,
    offset: int = 0,
    limit: int = 100,
    filters: TransactionFilters | None = None,
):
    """Get all transactions with pagination and filtering support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100)
        filters: Optional filters to apply to the query

    Returns:
        List of Transaction objects
    """
    if filters is None:
        return db.get_db_entities(Transaction, offset, limit, session)

    # Build query with filters
    query = select(Transaction)

    # Apply filters
    if filters.user_id is not None:
        query = query.where(Transaction.user_id == filters.user_id)

    if filters.category_id is not None:
        query = query.where(Transaction.category_id == filters.category_id)

    if filters.source_id is not None:
        query = query.where(Transaction.source_id == filters.source_id)

    if filters.state is not None:
        query = query.where(Transaction.state == filters.state)

    if filters.start_date is not None:
        query = query.where(Transaction.date >= filters.start_date)

    if filters.end_date is not None:
        query = query.where(Transaction.date <= filters.end_date)

    if filters.min_amount is not None:
        query = query.where(Transaction.amount >= filters.min_amount)

    if filters.max_amount is not None:
        query = query.where(Transaction.amount <= filters.max_amount)

    # Apply sorting
    if filters.sort_by:
        sort_field = getattr(Transaction, filters.sort_by, None)
        if sort_field is not None:
            if filters.sort_desc:
                query = query.order_by(col(sort_field).desc())
            else:
                query = query.order_by(sort_field)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    transactions = session.exec(query).all()
    return cast(list[Transaction], transactions)


async def create_transaction(session: SessionDep, transaction: CreateTransaction):
    return await _transaction_crud.create(session, transaction)


async def get_transaction(
    session: SessionDep,
    transaction_id: int,
):
    return await _transaction_crud.get_by_id(session, transaction_id)


async def update_transaction(
    session: SessionDep,
    id: int,
    transaction: UpdateTransaction,
):
    return await _transaction_crud.update(session, id, transaction)


async def delete_transaction(session: SessionDep, id: int):
    return await _transaction_crud.delete(session, id)

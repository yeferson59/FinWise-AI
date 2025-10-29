from app.db.session import SessionDep
from app.utils import db
from app.models.transaction import Transaction
from app.schemas.transaction import (
    CreateTransaction,
    UpdateTransaction,
    TransactionFilters,
)
from sqlmodel import select, col
from typing import cast


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
    trs = Transaction(**transaction.model_dump())
    db.create_db_entity(trs, session)
    return trs


async def get_transaction(
    session: SessionDep,
    transaction_id: int,
):
    return db.get_entity_by_id(Transaction, transaction_id, session)


async def update_transaction(
    session: SessionDep,
    id: int,
    transaction: UpdateTransaction,
):
    update_data = transaction.model_dump(exclude_unset=True)
    return db.update_db_entity(Transaction, id, update_data, session)


async def delete_transaction(session: SessionDep, id: int):
    transaction = await get_transaction(session, id)
    db.delete_db_entity(Transaction, id, session)
    return transaction

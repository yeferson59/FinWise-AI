from typing import Annotated
from fastapi import APIRouter, Path, Query
from datetime import datetime
from app.models.transaction import Transaction
from app.services import transaction
from app.db.session import SessionDep
from app.schemas.transaction import (
    CreateTransaction,
    UpdateTransaction,
    TransactionFilters,
)

router = APIRouter()


@router.get("")
async def get_transactions(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    user_id: Annotated[int | None, Query(ge=1)] = None,
    category_id: Annotated[int | None, Query(ge=1)] = None,
    source_id: Annotated[int | None, Query(ge=1)] = None,
    state: Annotated[str | None, Query()] = None,
    start_date: Annotated[datetime | None, Query()] = None,
    end_date: Annotated[datetime | None, Query()] = None,
    min_amount: Annotated[float | None, Query(ge=0)] = None,
    max_amount: Annotated[float | None, Query(ge=0)] = None,
    sort_by: Annotated[
        str | None, Query(pattern="^(date|amount|created_at|updated_at)$")
    ] = "date",
    sort_desc: Annotated[bool, Query()] = True,
) -> list[Transaction]:
    """Get all transactions with advanced filtering and pagination support.

    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        user_id: Filter by user ID (optional)
        category_id: Filter by category ID (optional)
        source_id: Filter by source ID (optional)
        state: Filter by transaction state (optional)
        start_date: Filter by start date - inclusive (optional)
        end_date: Filter by end date - inclusive (optional)
        min_amount: Filter by minimum amount (optional)
        max_amount: Filter by maximum amount (optional)
        sort_by: Field to sort by (date, amount, created_at, updated_at) (default: date)
        sort_desc: Sort in descending order (default: True)

    Returns:
        List of Transaction objects matching the filters

    Examples:
        - Get all transactions for user 1: ?user_id=1
        - Get transactions in a date range: ?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z
        - Get transactions by amount range: ?min_amount=100&max_amount=500
        - Get completed transactions: ?state=completed
        - Combine filters: ?user_id=1&category_id=5&state=completed&sort_by=amount&sort_desc=false
    """
    filters = TransactionFilters(
        user_id=user_id,
        category_id=category_id,
        source_id=source_id,
        state=state,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return await transaction.get_all_transactions(session, offset, limit, filters)


@router.post("")
async def create_transaction(
    session: SessionDep,
    create_transaction: CreateTransaction,
) -> Transaction:
    return await transaction.create_transaction(session, create_transaction)


@router.get("/{transaction_id}")
async def get_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
) -> Transaction:
    return await transaction.get_transaction(session, transaction_id)


@router.put("/{transaction_id}")
async def update_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
    update_transaction: UpdateTransaction,
) -> Transaction:
    return await transaction.update_transaction(
        session, transaction_id, update_transaction
    )


@router.delete("/{transaction_id}")
async def delete_transaction(
    session: SessionDep,
    transaction_id: Annotated[int, Path],
) -> Transaction:
    return await transaction.delete_transaction(session, transaction_id)

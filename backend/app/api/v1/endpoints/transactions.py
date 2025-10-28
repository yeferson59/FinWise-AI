from typing import Annotated
from fastapi import APIRouter, Path, Query
from app.models.transaction import Transaction
from app.services import transaction
from app.db.session import SessionDep
from app.schemas.transaction import CreateTransaction, UpdateTransaction

router = APIRouter()


@router.get("")
async def get_transactions(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[Transaction]:
    """Get all transactions with pagination support.
    
    Args:
        session: Database session
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
    
    Returns:
        List of Transaction objects
    """
    return await transaction.get_all_transactions(session, offset, limit)


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

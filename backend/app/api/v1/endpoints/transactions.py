from typing import Annotated
from fastapi import APIRouter, Path
from app.models.transaction import Transaction
from app.services import transaction
from app.db.session import SessionDep
from app.schemas.transaction import CreateTransaction, UpdateTransaction

router = APIRouter()


@router.get("")
async def get_transactions(session: SessionDep) -> list[Transaction]:
    return await transaction.get_all_transactions(session)


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

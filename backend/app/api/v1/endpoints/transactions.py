from fastapi import APIRouter
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
    transaction_create: CreateTransaction, session: SessionDep
) -> Transaction:
    return await transaction.create_transaction(session, transaction_create)


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: int, session: SessionDep) -> Transaction:
    return await transaction.get_transaction(session, transaction_id)


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: int, transaction_update: UpdateTransaction, session: SessionDep
) -> Transaction:
    return await transaction.update_transaction(
        session, transaction_id, transaction_update
    )


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: int, session: SessionDep) -> Transaction:
    return await transaction.delete_transaction(session, transaction_id)

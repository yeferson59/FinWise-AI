from app.db.session import SessionDep
from app.utils import db
from app.models.transaction import Transaction
from app.schemas.transaction import CreateTransaction, UpdateTransaction


async def get_all_transactions(session: SessionDep):
    return db.get_db_entities(Transaction, 0, 10, session)


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

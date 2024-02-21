from typing import Any
from uuid import UUID

from app.config.logging_settings import get_logger
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager
from app.exceptions.exception import ProcessingException
from app.schemas.base import Entity
from app.schemas.transaction import TransactionType

logger = get_logger(__name__)


def get_storage_data(transaction: Transaction) -> list[Entity | None]:
    if transaction.type != TransactionType.READ_ONLY:
        raise ProcessingException(f'Wrong transaction type: {transaction.type} to get storage data')

    storage_data: list[Entity | None] = transaction.get_storage_data()
    transaction_manager.close_transaction(transaction)
    return storage_data


# TODO decorator to rollback all transactions
def insert_entity(transaction: Transaction, value: Any) -> None:
    if transaction.type == TransactionType.READ_ONLY:
        raise ProcessingException(f'Wrong transaction type: {transaction.type} to insert entity')
    transaction.insert_entity(value)
    logger.info(f'Inserted entity: {value} to transaction: {transaction.id}')


# TODO decorator to rollback all transactions
def delete_entity(transaction: Transaction, id: UUID) -> None:
    if transaction.type == TransactionType.READ_ONLY:
        raise ProcessingException(f'Wrong transaction type: {transaction.type} to delete entity')

    transaction.delete_entity(id)
    logger.info(f'Deleted entity: {id} from transaction: {transaction.id}')

from uuid import UUID

from app.config.logging_settings import get_logger
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager

logger = get_logger(__name__)


def begin_transaction() -> UUID:
    transaction: Transaction = transaction_manager.create_transaction()
    return transaction.id


def transaction_commit() -> None:
    logger.info('Starting commit stage')
    transaction_manager.commit()
    logger.info('Finish commit stage')


def transaction_rollback() -> None:
    logger.info('Starting rollback stage')
    transaction_manager.rollback()
    logger.info('Finish rollback stage')

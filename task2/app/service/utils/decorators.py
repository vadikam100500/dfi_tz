from functools import wraps

from app.config.logging_settings import get_logger
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager

logger = get_logger(__name__)


def rollback_on_failure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        transaction: Transaction | None = args[0] if args else kwargs.get('transaction')
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not transaction:
                logger.error(f'Rollback_by_nested_transaction error: {exc.args}, '
                             f'transaction not found in args {args} or kwargs {kwargs}')
            transaction_manager.rollback_by_nested_transaction(transaction)
            raise exc
    return wrapper

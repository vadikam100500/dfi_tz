from functools import wraps

from app.config.logging_settings import get_logger
from app.core.transaction import Transaction

logger = get_logger(__name__)


def rollback_on_failure(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        transaction: Transaction | None = args[0] if args else kwargs.get('transaction')
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if not transaction:
                logger.error(f'Rollback on failure error: {exc.args}, '
                             f'transaction not found in args {args} or kwargs {kwargs}')
                raise exc

            transaction.rollback()
            raise exc
    return wrapper

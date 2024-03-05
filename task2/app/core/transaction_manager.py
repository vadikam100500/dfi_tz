from uuid import UUID

from app.config.logging_settings import get_logger
from app.core.transaction import Transaction
from app.exceptions.exception import NotFoundEntity, ProcessingException
from app.schemas.transaction import TransactionStatus, TransactionType

logger = get_logger(__name__)


class TransactionManager:
    _transactions: list[Transaction] = []
    _read_only_transactions: dict[UUID, Transaction] = {}

    def _get_pending_nested_transaction(self, transaction: Transaction) -> Transaction | None:
        if not transaction.nested_transaction:
            if transaction.status == TransactionStatus.PENDING:
                return transaction
            return None

        nested_transaction: Transaction | None = self._get_pending_nested_transaction(transaction.nested_transaction)
        if nested_transaction:
            return nested_transaction

        if not nested_transaction and transaction.status == TransactionStatus.PENDING:
            return transaction

        return None

    def get_transaction(self) -> Transaction:
        if not self._transactions:
            raise NotFoundEntity('There is no opened transactions. Begin new one.')

        last_transaction: Transaction = self._transactions[-1]
        if last_transaction.status != TransactionStatus.PENDING:
            raise NotFoundEntity('There is no pending transactions. Begin new one.')

        transaction = None

        if last_transaction.nested_transaction:
            transaction: Transaction | None = self._get_pending_nested_transaction(last_transaction.nested_transaction)

        if not transaction:
            transaction: Transaction = last_transaction

        return transaction

    def get_read_only_transaction(self) -> Transaction:
        transaction = Transaction(type=TransactionType.READ_ONLY)
        self._read_only_transactions[transaction.id] = transaction
        return transaction

    def close_transaction(self, transaction: Transaction) -> None:
        match transaction.type:
            case TransactionType.READ_ONLY:
                self._read_only_transactions.pop(transaction.id)
            case _:
                pass

    def _create_main_transaction(self) -> Transaction:
        transaction = Transaction()
        logger.info(f'Created main transaction: {transaction.id}')

        self._transactions.append(transaction)
        return transaction

    def create_transaction(self) -> Transaction:
        if not self._transactions or self._transactions[-1].status != TransactionStatus.PENDING:
            return self._create_main_transaction()

        main_transaction: Transaction = self._transactions[-1]

        last_pending_transaction: Transaction | None = self._get_pending_nested_transaction(main_transaction)
        if not last_pending_transaction:
            last_pending_transaction: Transaction = main_transaction

        new_transaction = Transaction(type=TransactionType.NESTED)
        last_pending_transaction.nested_transaction = new_transaction
        logger.info(f'Created nested transaction: {new_transaction.id} for transaction: {last_pending_transaction.id} '
                    f'with main transaction: {main_transaction.id}')

        return new_transaction

    def _get_main_transaction(self, action: TransactionStatus) -> Transaction:
        if not self._transactions:
            raise ProcessingException(f'There is no transactions. Nothing to {action}.')

        for transaction in reversed(self._transactions):
            if transaction.status == TransactionStatus.PENDING:
                return transaction

        raise ProcessingException(f'There is no pending transactions. Nothing to {action}.')

    def _get_transaction_for_action(self, action: TransactionStatus) -> Transaction:
        main_transaction: Transaction = self._get_main_transaction(action)

        if main_transaction.nested_transaction:
            transaction: Transaction | None = self._get_pending_nested_transaction(main_transaction)
            if not transaction:
                raise ProcessingException(f'There is no pending nested transactions. Nothing to {action}.')
        else:
            transaction = main_transaction

        if transaction.type == TransactionType.MAIN:
            self._transactions.remove(transaction)

        return transaction

    def commit(self) -> None:
        transaction: Transaction = self._get_transaction_for_action(action=TransactionStatus.COMMIT)
        transaction.status = TransactionStatus.COMMIT

    def rollback(self) -> None:
        transaction: Transaction = self._get_transaction_for_action(action=TransactionStatus.ROLLBACK)
        transaction.status = TransactionStatus.ROLLBACK
        transaction.rollback()


transaction_manager = TransactionManager()

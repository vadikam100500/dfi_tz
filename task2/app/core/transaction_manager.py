from uuid import UUID

from app.config.logging_settings import get_logger
from app.core.storage import storage
from app.core.transaction import Transaction
from app.exceptions.exception import ProcessingException
from app.schemas.transaction import TransactionStatus, TransactionType

logger = get_logger(__name__)


class TransactionManager:
    _transactions: dict[Transaction, list[Transaction]] = {}

    _in_change_stage: set[UUID] = {}
    _last_changed_transactions: set[Transaction] = {}

    _read_only_transactions: dict[UUID, Transaction] = {}

    def _get_pending_transaction(self) -> Transaction | None:
        for transaction in reversed(self._transactions):  # py 3.10 ordered dict
            if transaction.status == TransactionStatus.PENDING and transaction.id not in self._in_change_stage:
                # without ready_to_commit status to be shured that this transaction is not in change stage
                return transaction
        return None

    def _create_transaction_with_nested(self) -> Transaction:
        main_transaction = Transaction()
        nested_transaction = Transaction(type=TransactionType.NESTED)
        self._transactions[main_transaction] = [nested_transaction]
        return nested_transaction

    def _get_pending_nested_transaction(self) -> Transaction:
        main_transaction: Transaction | None = self._get_pending_transaction()
        if main_transaction:
            nested_transactions: list[Transaction] = self._transactions[main_transaction]
            for transaction in reversed(nested_transactions):
                if transaction.status == TransactionStatus.PENDING:
                    return transaction

            transaction = Transaction(type=TransactionType.NESTED)
            self._transactions[main_transaction].append(transaction)
        else:
            transaction: Transaction = self._create_transaction_with_nested()
        return transaction

    def get_transaction(self) -> Transaction:
        if not self._transactions:
            transaction: Transaction = self._create_transaction_with_nested()
        else:
            transaction: Transaction = self._get_pending_nested_transaction()
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

    def _remove_main_transaction(self, transaction: Transaction) -> None:
        try:
            self._transactions.pop(transaction)
        except KeyError:
            pass

    def commit(self) -> None:
        try:
            main_transaction, nested_transactions = next(iter(self._transactions.items()))
        except StopIteration:
            raise ProcessingException('No transactions in commit stage.')

        main_transaction.status = TransactionStatus.COMMIT

        transactions_ids = {main_transaction.id} | {nested_transaction.id for nested_transaction in nested_transactions}
        if self._in_change_stage:
            self._in_change_stage |= transactions_ids
        else:
            self._in_change_stage = transactions_ids

        try:
            [nested_transaction.commit() for nested_transaction in nested_transactions]
        except Exception as exc:
            logger.error(f'Nested transactions commit error transactions_ids: {transactions_ids}, exc: {exc.args}')
            self._remove_main_transaction(main_transaction)
            [nested_transaction.rollback_stage() for nested_transaction in nested_transactions]
            raise exc

        self._remove_main_transaction(main_transaction)
        self._last_changed_transactions = {*nested_transactions}
        self._in_change_stage -= transactions_ids

        try:
            storage.commit()
        except Exception as exc:
            logger.error(f'Storage commit error transactions_ids: {transactions_ids}, exc: {exc.args}')
            self.rollback()

    def rollback(self) -> None:
        [tranasction.rollback() for tranasction in self._last_changed_transactions]
        logger.info(f'Rollback transactions: {[tranasction.id for tranasction in self._last_changed_transactions]}')
        self._last_changed_transactions = {}

    def rollback_by_nested_transaction(self, transaction: Transaction) -> None:
        main_transaction = None
        nested_transactions = None
        for transaction, transaction_nested in self._transactions.items():
            if transaction == transaction or transaction in transaction_nested:
                main_transaction, nested_transactions = transaction, transaction_nested
                break

        if not main_transaction:
            raise ProcessingException(f'System error: transaction {transaction.id} not found '
                                      'during rollback_by_nested_transaction')

        self._transactions.pop(transaction)
        [nested_transaction.rollback() for nested_transaction in nested_transactions]
        logger.info(f'Nested transactions for transaction [{main_transaction.id}] deleted: '
                    f'{[nested_transaction.id for nested_transaction in nested_transactions]}')


transaction_manager = TransactionManager()

from uuid import UUID

import pytest

from app.core.storage import storage
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager
from app.exceptions.exception import NotFoundEntity, ProcessingException
from app.schemas.transaction import TransactionStatus, TransactionType
from app.service import transaction_service


def test_begin_transaction():
    # When
    transaction_id: UUID = transaction_service.begin_transaction()
    transaction: Transaction = transaction_manager.get_transaction()

    # Then
    assert transaction
    assert transaction.id
    assert transaction.id == transaction_id
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.type == TransactionType.MAIN
    assert not transaction.nested_transaction


def test_begin_nested_transaction():
    # Given
    _: UUID = transaction_service.begin_transaction()
    transaction_main: Transaction = transaction_manager.get_transaction()

    # When
    transaction1_id: UUID = transaction_service.begin_transaction()
    transaction1: Transaction = transaction_manager.get_transaction()

    transaction2_id: UUID = transaction_service.begin_transaction()
    transaction2: Transaction = transaction_manager.get_transaction()

    # Then
    for transaction in (transaction1, transaction2):
        assert transaction
        assert transaction.id
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.type == TransactionType.NESTED

    assert transaction1.id == transaction1_id
    assert transaction2.id == transaction2_id

    assert transaction_main.nested_transaction == transaction1
    assert transaction1.nested_transaction == transaction2


def test_get_last_pending_transaction():
    # Given
    _: UUID = transaction_service.begin_transaction()
    _: Transaction = transaction_manager.get_transaction()

    _: UUID = transaction_service.begin_transaction()
    transaction1: Transaction = transaction_manager.get_transaction()

    _: UUID = transaction_service.begin_transaction()
    transaction2: Transaction = transaction_manager.get_transaction()
    transaction2.status = TransactionStatus.COMMIT

    # When
    transaction: Transaction = transaction_manager.get_transaction()

    # Then
    assert transaction
    assert transaction == transaction1


def test_begin_transaction_after_not_pending_transaction():
    # Given
    _: UUID = transaction_service.begin_transaction()
    _: Transaction = transaction_manager.get_transaction()

    _: UUID = transaction_service.begin_transaction()
    transaction1: Transaction = transaction_manager.get_transaction()

    _: UUID = transaction_service.begin_transaction()
    transaction2: Transaction = transaction_manager.get_transaction()
    transaction2.status = TransactionStatus.COMMIT

    # When
    _: UUID = transaction_service.begin_transaction()
    transaction: Transaction = transaction_manager.get_transaction()

    # Then
    assert transaction1.nested_transaction == transaction


def test_transaction_commit_without_transaction():
    with pytest.raises(ProcessingException) as exc:
        # When
        transaction_service.transaction_commit()
    # Then
    assert 'There is no transactions. Nothing to COMMIT.' in str(exc.value)


def test_transaction_commit_without_pending_transactions(only_commit_status_transactions):
    with pytest.raises(ProcessingException) as exc:
        # When
        transaction_service.transaction_commit()

    # Then
    assert 'There is no pending transactions. Nothing to COMMIT.' in str(exc.value)


def test_transaction_commit():
    # Given
    _: UUID = transaction_service.begin_transaction()
    main_transaction: Transaction = transaction_manager.get_transaction()

    _: UUID = transaction_service.begin_transaction()
    transaction: Transaction = transaction_manager.get_transaction()

    transaction.insert_entity(value=123)
    assert len(storage._storage) == 1

    # When
    transaction_service.transaction_commit()
    _: UUID = transaction_service.begin_transaction()
    new_transaction: Transaction = transaction_manager.get_transaction()

    # Then
    assert len(storage._storage) == 1
    assert list(storage._storage.values()) == [123]

    assert transaction.status == TransactionStatus.COMMIT
    assert main_transaction.status == TransactionStatus.PENDING
    assert main_transaction.nested_transaction
    assert main_transaction.nested_transaction == new_transaction
    assert new_transaction.status == TransactionStatus.PENDING


def test_transaction_rollback_without_transaction():
    with pytest.raises(ProcessingException) as exc:
        # When
        transaction_service.transaction_rollback()
    # Then
    assert 'There is no transactions. Nothing to ROLLBACK.' in str(exc.value)


def test_transaction_rollback_without_pending_transactions(only_commit_status_transactions):
    with pytest.raises(ProcessingException) as exc:
        # When
        transaction_service.transaction_rollback()

    # Then
    assert 'There is no pending transactions. Nothing to ROLLBACK.' in str(exc.value)


def test_transaction_rollback():
    # Given
    _: UUID = transaction_service.begin_transaction()
    main_transaction: Transaction = transaction_manager.get_transaction()
    main_transaction.insert_entity(value=123)
    assert len(storage._storage) == 1

    _: UUID = transaction_service.begin_transaction()
    transaction: Transaction = transaction_manager.get_transaction()
    transaction.insert_entity(value=321)
    assert len(storage._storage) == 2
    assert list(storage._storage.values()) == [123, 321]

    # When
    transaction_service.transaction_rollback()
    _: UUID = transaction_service.begin_transaction()
    new_transaction: Transaction = transaction_manager.get_transaction()

    # Then
    assert len(storage._storage) == 1
    assert list(storage._storage.values()) == [123]

    assert transaction.status == TransactionStatus.ROLLBACK
    assert main_transaction.status == TransactionStatus.PENDING
    assert main_transaction.nested_transaction
    assert main_transaction.nested_transaction == new_transaction
    assert new_transaction.status == TransactionStatus.PENDING


def test_transaction_insert_after_rollback():
    # Given
    _: UUID = transaction_service.begin_transaction()
    main_transaction: Transaction = transaction_manager.get_transaction()
    main_transaction.insert_entity(value=123)
    assert len(storage._storage) == 1

    _: UUID = transaction_service.begin_transaction()
    transaction: Transaction = transaction_manager.get_transaction()
    transaction.insert_entity(value=321)
    assert len(storage._storage) == 2
    assert list(storage._storage.values()) == [123, 321]

    # When
    transaction_service.transaction_rollback()
    transaction_to_insert: Transaction = transaction_manager.get_transaction()
    transaction_to_insert.insert_entity(value=456)

    # Then
    assert transaction_to_insert == main_transaction
    assert transaction_to_insert.status == TransactionStatus.PENDING
    assert len(transaction_to_insert.action_log) == 2
    assert list(storage._storage.values()) == [123, 456]

    # When
    transaction_service.transaction_commit()

    # Then
    assert transaction_to_insert.status == TransactionStatus.COMMIT

    with pytest.raises(NotFoundEntity) as exc:
        transaction_manager.get_transaction()
    assert 'There is no opened transactions. Begin new one.' in str(exc.value)

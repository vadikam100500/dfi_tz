from uuid import UUID, uuid4

import pytest

from app.core.storage import storage
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager
from app.exceptions.exception import ProcessingException
from app.schemas.transaction import TransactionType
from app.service import storage_service


def test_get_empty_storage_data(client):
    # When
    response = client.get("/storage/select")

    # Then
    assert response.status_code == 200
    assert response.json() == []


def test_get_storage_data_with_incorrect_transaction_type():
    for transaction_type in (TransactionType.MAIN, TransactionType.NESTED):
        # Given
        transaction = Transaction(type=transaction_type)

        with pytest.raises(ProcessingException) as exc:
            # When
            storage_service.get_storage_data(transaction)
        # Then
        assert f'Wrong transaction type: {transaction_type} to get storage data' in str(exc.value)


def tests_get_storage_data(client):
    # Given
    storage_data = {uuid4(): value for value in range(3)}
    storage._storage = storage_data

    # When
    response = client.get("/storage/select")

    # Then
    assert response.status_code == 200
    assert response.json() == [{'id': str(key), 'value': value} for key, value in storage_data.items()]
    assert not transaction_manager._transactions
    assert not transaction_manager._read_only_transactions


def test_insert_entity_without_transaction(client):
    # When
    response = client.post("/storage/insert",
                           headers={"token": '1234'},
                           json={"value": 4321})

    # Then
    assert response.status_code == 404
    assert response.json() == {'message': 'There is no opened transactions. Begin new one.'}


def test_insert_entity_with_incorrect_transaction():
    # Given
    transaction = Transaction(type=TransactionType.READ_ONLY)

    with pytest.raises(ProcessingException) as exc:
        # When
        storage_service.insert_entity(transaction=transaction, value=1234)

    # Then
    assert f'Wrong transaction type: {transaction.type} to insert entity' in str(exc.value)


def test_insert_entity():
    # Given
    transaction = Transaction()

    # When
    storage_service.insert_entity(transaction=transaction, value=1234)

    # Then
    assert len(storage._storage) == 1
    for key, value in storage._storage.items():
        assert isinstance(key, UUID)
        assert value == 1234


def test_delete_entity_without_transaction(client):
    # When
    response = client.delete("/storage/delete",
                             headers={"token": '1234', "id": str(uuid4())})

    # Then
    assert response.status_code == 404
    assert response.json() == {'message': 'There is no opened transactions. Begin new one.'}


def test_delete_entity_with_incorrect_transaction():
    # Given
    transaction = Transaction(type=TransactionType.READ_ONLY)

    with pytest.raises(ProcessingException) as exc:
        # When
        storage_service.delete_entity(transaction=transaction, id=uuid4())

    # Then
    assert f'Wrong transaction type: {transaction.type} to delete entity' in str(exc.value)


def test_delete_entity():
    # Given
    transaction = Transaction()

    storage_data = {uuid4(): value for value in range(5)}
    storage._storage = storage_data

    key_to_test = list(storage_data.keys())[3]

    # When
    storage_service.delete_entity(transaction=transaction, id=key_to_test)

    # Then
    assert len(storage._storage) == 4
    assert storage._storage.get(key_to_test) is None
    assert list(storage._storage.values()) == [0, 1, 2, 4]

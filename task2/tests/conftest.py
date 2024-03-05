import pytest
from fastapi.testclient import TestClient

from app.core.storage import storage
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager
from app.main import app
from app.schemas.transaction import TransactionStatus, TransactionType


@pytest.fixture(autouse=True)
def setup():

    yield

    storage._storage = {}
    transaction_manager._transactions = []
    transaction_manager._read_only_transactions = {}


@pytest.fixture
def client():
    client = TestClient(app)

    yield client


@pytest.fixture
def only_commit_status_transactions():
    fixture_transactions = []
    for _ in range(4):
        main_transaction = Transaction()
        nested_transaction = Transaction(type=TransactionType.NESTED)
        nested_transaction.status = TransactionStatus.COMMIT
        main_transaction.status = TransactionStatus.COMMIT
        main_transaction.nested_transaction = nested_transaction
        fixture_transactions.append(main_transaction)

    transaction_manager._transactions = fixture_transactions

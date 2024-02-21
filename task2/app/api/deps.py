from typing import Any

from fastapi import Header

from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager


async def get_transaction() -> Transaction:
    transaction: Transaction = transaction_manager.get_transaction()
    return transaction


async def get_read_only_transaction() -> Transaction:
    transaction: Transaction = transaction_manager.get_read_only_transaction()
    return transaction


async def get_permission(token: Any = Header()) -> Any:
    # some logic for check permission
    return token

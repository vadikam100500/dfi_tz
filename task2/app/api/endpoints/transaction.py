from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_permission
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager

router = APIRouter()


@router.get("/begin", response_model=UUID)
async def begin_transaction():
    transaction: Transaction = transaction_manager.get_transaction()
    return transaction.id


@router.post("/commit")
async def transaction_commit(permission: Any = Depends(get_permission)):
    transaction_manager.commit()


@router.post("/rollback")
async def rollback_transaction(permission: Any = Depends(get_permission)):
    transaction_manager.rollback()

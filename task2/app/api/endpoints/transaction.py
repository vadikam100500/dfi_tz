from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_permission
from app.service import transaction_service

router = APIRouter()


@router.get("/begin", response_model=UUID)
async def begin_transaction():
    transaction_id: UUID = transaction_service.begin_transaction()
    return transaction_id


@router.post("/commit")
async def transaction_commit(permission: Any = Depends(get_permission)):
    transaction_service.transaction_commit()


@router.post("/rollback")
async def transaction_rollback(permission: Any = Depends(get_permission)):
    transaction_service.transaction_rollback()

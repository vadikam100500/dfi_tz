from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_permission
from app.config.logging_settings import get_logger
from app.core.transaction import Transaction
from app.core.transaction_manager import transaction_manager

logger = get_logger(__name__)

router = APIRouter()


@router.get("/begin", response_model=UUID)
async def begin_transaction():
    transaction: Transaction = transaction_manager.get_transaction()
    return transaction.id


@router.post("/commit")
async def transaction_commit(permission: Any = Depends(get_permission)):
    logger.info('Starting commit stage')
    transaction_manager.commit()
    logger.info('Finish commit stage')


@router.post("/rollback")
async def rollback_transaction(permission: Any = Depends(get_permission)):
    logger.info('Starting rollback stage')
    transaction_manager.rollback()
    logger.info('Finish rollback stage')

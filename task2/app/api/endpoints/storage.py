from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_permission, get_read_only_transaction, get_transaction
from app.core.transaction import Transaction
from app.schemas.base import Entity
from app.service import storage_service

router = APIRouter()


@router.get("/select", response_model=list[Entity | None])
async def get_entities(transaction: Transaction = Depends(get_read_only_transaction)):
    entities: list[Entity | None] = storage_service.get_storage_data(transaction)
    return entities


@router.post("/insert")
async def insert_entity(value: Any,
                        permission: Any = Depends(get_permission),
                        transaction: Transaction = Depends(get_transaction)):
    '''Return status of insert: 200, 422 or 500'''
    storage_service.insert_entity(transaction=transaction, value=value)


@router.delete("/delete")
async def delete_entity(id: UUID,
                        permission: Any = Depends(get_permission),
                        transaction: Transaction = Depends(get_transaction)):
    '''Return status of delete: 200, 404, 422 or 500'''
    storage_service.delete_entity(transaction=transaction, id=id)

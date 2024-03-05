from typing import Any
from uuid import UUID, uuid4

from app.config.logging_settings import get_logger
from app.core.storage import storage
from app.exceptions.exception import NotFoundEntity
from app.schemas.base import Entity
from app.schemas.transaction import TransactionMethod, TransactionStatus, TransactionType

logger = get_logger(__name__)


class Transaction:
    def __init__(self, type: TransactionType = TransactionType.MAIN):
        self.type: TransactionType = type
        self.status = TransactionStatus.PENDING
        self.id: UUID = uuid4()
        self.nested_transaction: Transaction | None = None

        self.action_log: list[tuple[Entity, TransactionMethod]] = []

    def get_storage_data(self) -> list[Entity | None]:
        storage_data: list[Entity | None] = storage.get_storage_data()
        return storage_data

    def insert_entity(self, value: Any) -> None:
        new_entity: Entity = storage.insert_entity(entity_id=uuid4(), value=value)
        logger.info(f'Inserted entity: {new_entity} by transaction: {self.id}')

        self.action_log.append((new_entity, TransactionMethod.INSERT))
        return new_entity

    def delete_entity(self, id: UUID) -> None:
        value_to_delete: Entity | None = storage.get_entity_by_id(id)
        if not value_to_delete:
            raise NotFoundEntity(f'Value {id} not exists in storage.')

        storage.delete_entity(id)
        logger.info(f'Deleted entity: {value_to_delete} by transaction: {self.id}')

        self.action_log.append((value_to_delete, TransactionMethod.DELETE))

    def rollback(self) -> None:
        for (entity, method) in reversed(self.action_log):
            try:

                match method:
                    case TransactionMethod.INSERT:
                        storage.delete_entity(entity.id)
                    case TransactionMethod.DELETE:
                        storage.insert_entity(entity.id, entity.value)

                logger.info(f'Rollback entity: {entity} by transaction: {self.id}')

            except Exception as exc:
                logger.error(f'Rollback error: {exc.args}')

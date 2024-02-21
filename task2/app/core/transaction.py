from typing import Any
from uuid import UUID, uuid4

from app.core.storage import storage
from app.exceptions.exception import NotFoundEntity, ProcessingException
from app.schemas.base import Entity
from app.schemas.transaction import TransactionMethod, TransactionStatus, TransactionType


class Transaction:
    def __init__(self, type: TransactionType = TransactionType.MAIN):
        self.type: TransactionType = type
        self.status = TransactionStatus.PENDING
        self.id: UUID = uuid4()

        self.entity: Entity | None = None
        self.method: TransactionMethod | None = None

    def get_storage_data(self) -> list[Entity | None]:
        storage_data: list[Entity | None] = storage.get_storage_data()
        return storage_data

    def insert_entity(self, value: Any) -> None:
        if self.entity or self.method:
            raise ProcessingException(f'System error: entity {self.entity} or method {self.method} '
                                      f'already exists in this transaction, value {value} not inserted')

        is_value_exists: Entity | None = storage.get_entity_by_value(value)
        if is_value_exists:
            raise ProcessingException(f'Value {value} already exists in storage.')

        self.entity = Entity(id=uuid4(), value=value)
        self.method = TransactionMethod.INSERT
        self.status = TransactionStatus.READY_TO_COMMIT

    def delete_entity(self, id: UUID) -> None:
        if self.entity or self.method:
            raise ProcessingException(f'System error: transaction {self.id} already in delete stage'
                                      f'not deleted value_id {id}')
        value_to_delete: Entity | None = storage.get_entity_by_id(id)
        if not value_to_delete:
            raise NotFoundEntity(f'Value {id} not exists in storage.')

        self.entity: Entity = value_to_delete
        self.method = TransactionMethod.DELETE
        self.status = TransactionStatus.READY_TO_COMMIT

    def commit(self) -> None:
        if not any((self.entity, self.method)):
            raise ProcessingException(f'System error: entity {self.entity} or method {self.method} not set')

        self.status = TransactionStatus.COMMIT

        storage.stage_commit(entity=self.entity, method=self.method)

    def rollback_stage(self) -> None:
        self.status = TransactionStatus.ROLLBACK
        storage.stage_rollback(entity=self.entity)

    def rollback(self) -> None:
        self.status = TransactionStatus.ROLLBACK
        storage.rollback(entity=self.entity, method=self.method)

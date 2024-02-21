from typing import Any
from uuid import UUID

from app.schemas.base import Entity
from app.schemas.transaction import TransactionMethod


class Storage:
    _instance = None

    _storage: dict[UUID, Any] = {}
    _stage_storage: dict[Entity, TransactionMethod] = {}

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def get_storage_data(self) -> list[Entity | None]:
        serialized_storage = [Entity(id=key, value=value) for key, value in self._storage.items()]
        return serialized_storage

    def get_entity_by_value(self, value: Any) -> Entity | None:
        for key, value in self._storage.items():
            if value == value:
                need_entity = Entity(id=key, value=value)
                return need_entity
        return None

    def get_entity_by_id(self, id: UUID) -> Entity | None:
        value: Any = self._storage.get(id)
        if value is None:
            return value
        need_entity = Entity(id=id, value=value)
        return need_entity

    def stage_commit(self, entity: Entity, method: TransactionMethod) -> None:
        self._stage_storage[entity] = method

    def stage_rollback(self, entity: Entity) -> None:
        try:
            self._stage_storage.pop(entity)
        except KeyError:
            pass

    def commit(self) -> None:
        for entity, method in self._stage_storage.items():
            match method:
                case TransactionMethod.INSERT:
                    self._storage[entity.id] = entity.value
                case TransactionMethod.DELETE:
                    self._storage.pop(entity.id)

    def rollback(self, entity: Entity, method: TransactionMethod) -> None:
        match method:
            case TransactionMethod.INSERT:
                try:
                    self._storage.pop(entity.id)
                except KeyError:
                    pass
            case TransactionMethod.DELETE:
                self._storage[entity.id] = entity.value


storage = Storage()

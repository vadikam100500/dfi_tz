from typing import Any
from uuid import UUID

from app.schemas.base import Entity


class Storage:
    _instance = None

    _storage: dict[UUID, Any] = {}

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def get_storage_data(self) -> list[Entity | None]:
        serialized_storage = [Entity(id=key, value=value) for key, value in self._storage.items()]
        return serialized_storage

    def insert_entity(self, entity_id: UUID, value: Any) -> Entity:
        self._storage[entity_id] = value
        return Entity(id=entity_id, value=value)

    def delete_entity(self, id: UUID) -> None:
        self._storage.pop(id)

    def get_entity_by_id(self, id: UUID) -> Entity | None:
        value: Any = self._storage.get(id)
        if value is None:
            return value
        need_entity = Entity(id=id, value=value)
        return need_entity


storage = Storage()

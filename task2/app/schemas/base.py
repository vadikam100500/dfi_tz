from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID


class EnumBaseUpper(str, Enum):
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value == value.upper():
                return member
        return None


@dataclass
class Entity:
    id: UUID
    value: Any

    def __hash__(self) -> int:
        return hash(str(self.id))

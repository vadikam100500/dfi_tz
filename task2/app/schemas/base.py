from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from typing import Any


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

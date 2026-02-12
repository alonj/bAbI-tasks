from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(eq=False)
class Entity:
    name: str
    properties: Dict[str, Any] | None = None
    carry: int = 0
    size: int = 0
    is_thing: bool = True

    def __post_init__(self) -> None:
        if self.properties:
            for key, value in self.properties.items():
                setattr(self, key, value)

    def __str__(self) -> str:
        return self.name

    def can_hold(self, entity: "Entity") -> bool:
        return self.size >= self.carry + entity.size

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Question:
    kind: str
    args: Any
    support: Any

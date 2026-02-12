from __future__ import annotations

from typing import Any


class Rule:
    def perform(self, world: Any) -> None:
        return

    def is_applicable(self, clause: Any, knowledge: Any, story: Any) -> bool:
        return True

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any) -> None:
        return

from __future__ import annotations

from typing import Any

from .knowledge import Knowledge
from .stringify import stringify


class Task:
    def generate(self, config: dict[str, Any] | None = None) -> str:
        config = config or {}
        world = self.new_world(config)
        story, knowledge = self.generate_story(world, Knowledge(world), [], config)
        return stringify(story, knowledge, config)

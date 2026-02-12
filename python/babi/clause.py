from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


@dataclass(eq=False)
class Clause:
    world: Any
    truth_value: bool
    actor: Any
    action: Any
    args: list[Any] = field(default_factory=list)

    def __init__(self, world: Any, truth_value: bool, actor: Any, action: Any, *args: Any):
        self.world = world
        self.truth_value = truth_value
        self.actor = actor
        self.action = action
        self.args = list(args)

    def is_valid(self) -> bool:
        return self.action.is_valid(self.world, self.actor, *self.args)

    def perform(self) -> None:
        if self.truth_value:
            self.action.perform(self.world, self.actor, *self.args)


    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Clause):
            return NotImplemented
        return (
            self.world == other.world
            and self.actor == other.actor
            and self.args == other.args
        )

    @classmethod
    def sample_valid(
        cls,
        world: Any,
        truth_values: Sequence[bool],
        actors: Sequence[Any],
        actions: Sequence[Any],
        *arg_pools: Sequence[Any],
    ) -> "Clause | None":
        for _ in range(100):
            truth_value = random.choice(truth_values)
            actor = random.choice(actors)
            action = random.choice(actions)
            args = [random.choice(pool) for pool in arg_pools]
            clause = cls(world, truth_value, actor, action, *args)
            if clause.is_valid():
                return clause
        return None

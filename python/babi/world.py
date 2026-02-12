from __future__ import annotations

from typing import Any, Callable

from .actions import actions
from .clause import Clause
from .entity import Entity
from .utilities import split


class World:
    def __init__(self, entities: dict[str, Entity] | None = None, world_actions: dict[str, Any] | None = None):
        self.entities = entities or {}
        if "god" not in self.entities:
            self.create_entity("god", {"is_god": True})
        self.actions = world_actions or actions

    def god(self) -> Entity:
        return self.entities["god"]

    def load(self, fname: str) -> None:
        with open(fname, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.perform_command(f"god {line}")

    def perform_command(self, command: str) -> None:
        actor_id, action, *raw_args = split(command)
        actor = self.entities[actor_id]
        args = [self.entities.get(arg, arg) for arg in raw_args]
        self.perform_action(action, actor, *args)

    def perform_action(self, action: str, actor: Entity, *args: Any) -> None:
        clause = Clause(self, True, actor, self.actions[action], *args)
        clause.perform()

    def create_entity(self, id_: str, properties: dict[str, Any] | None = None, name: str | None = None) -> Entity:
        if id_ in self.entities:
            raise ValueError("id already exists")
        entity = Entity(name or id_, properties)
        self.entities[id_] = entity
        return entity

    def get(self, predicate: Callable[[Entity], bool]):
        return [entity for entity in self.entities.values() if predicate(entity)]

    def get_actors(self):
        return [e for e in self.entities.values() if getattr(e, "is_actor", False) and getattr(e, "is_god", False)]

    def get_locations(self):
        return [e for e in self.entities.values() if getattr(e, "is_location", False)]

    def get_objects(self):
        return [e for e in self.entities.values() if getattr(e, "is_thing", False) and getattr(e, "is_gettable", False)]

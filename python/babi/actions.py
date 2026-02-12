from __future__ import annotations

from typing import Any


DIRECTIONS = {"n", "ne", "e", "se", "s", "sw", "w", "nw", "u", "d"}
NUMERIC_RELATIONS = {"size", "x", "y", "z"}
OPPOSITE_DIRECTIONS = {
    "n": "s",
    "ne": "sw",
    "e": "w",
    "se": "nw",
    "s": "n",
    "sw": "ne",
    "w": "e",
    "nw": "se",
    "u": "d",
    "d": "u",
}


def _is_number(value: Any) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


class Action:
    def __str__(self) -> str:
        return self.__class__.__name__


class Get(Action):
    def is_valid(self, world: Any, a0: Any, a1: Any, a2: Any = None, a3: Any = None) -> bool:
        if not (a0 and getattr(a0, "is_actor", False) and a1 and getattr(a1, "is_thing", False)):
            return False
        if not (getattr(a1, "is_gettable", False) and a0.can_hold(a1)):
            return False
        if a2:
            if a2 == "from" and a3 and getattr(a3, "is_thing", False):
                if a0.is_in != a3.is_in or a3.is_in == a0:
                    return False
                if a1.is_in != a3:
                    return False
            elif not (a2 == "count" and _is_number(a3)):
                return False
        elif a0.is_in != a1.is_in:
            return False
        return True

    def perform(self, world: Any, a0: Any, a1: Any, a2: Any = None, a3: Any = None) -> None:
        a1.is_in = a0
        a0.carry += a1.size
        if a2 == "from":
            a3.carry -= a1.size

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, a0: Any, a1: Any, *_: Any) -> None:
        if clause.truth_value:
            knowledge[a1].set("is_in", a0, True, {clause})


class Drop(Action):
    def is_valid(self, world: Any, a0: Any, a1: Any) -> bool:
        if not (a1 and getattr(a0, "is_actor", False) and getattr(a1, "is_thing", False)):
            return False
        return a1.is_in == a0

    def perform(self, world: Any, a0: Any, a1: Any) -> None:
        a1.is_in = a0.is_in
        a0.carry -= a1.size

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, a0: Any, a1: Any) -> None:
        if clause.truth_value:
            if knowledge[a0].values.get("is_in"):
                knowledge[a1].rawset("is_in", knowledge[a0].values["is_in"], {clause})
            else:
                knowledge[a1].rawset("is_in", [])


class Create(Action):
    def is_valid(self, world: Any, a0: Any, a1: Any) -> bool:
        return bool(a0 and getattr(a0, "is_god", False) and a1 not in world.entities)

    def perform(self, world: Any, a0: Any, a1: Any) -> None:
        world.create_entity(a1)


class SetProperty(Action):
    def is_valid(self, world: Any, actor: Any, a0: Any, rel: str, a1: Any = None) -> bool:
        if not (actor and getattr(actor, "is_god", False) and a0 and rel):
            return False
        if rel in NUMERIC_RELATIONS and not _is_number(a1):
            return False
        return True

    def perform(self, world: Any, actor: Any, a0: Any, rel: str, a1: Any = None) -> None:
        value = True if a1 is None else a1
        if _is_number(value):
            value = int(float(value))
        if rel == "is_in":
            if getattr(a0, "is_in", None):
                a0.is_in.carry -= a0.size
            value.carry += a0.size
        setattr(a0, rel, value)

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, actor: Any, a0: Any, rel: str, a1: Any = None) -> None:
        knowledge[a0].set(rel, a1, clause.truth_value, {clause})


class SetDir(Action):
    def is_valid(self, world: Any, actor: Any, a0: Any, direction: str, a1: Any) -> bool:
        if not (actor and getattr(actor, "is_god", False)):
            return False
        if not (a0 and getattr(a0, "is_thing", False) and a1 and getattr(a1, "is_thing", False)):
            return False
        if direction not in DIRECTIONS:
            return False
        if not all(hasattr(e, k) for e in (a0, a1) for k in ("x", "y", "z")):
            return False
        dx, dy, dz = a1.x - a0.x, a1.y - a0.y, a1.z - a0.z
        checks = {"n": dy > 0, "s": dy < 0, "e": dx > 0, "w": dx < 0, "u": dz > 0, "d": dz < 0}
        return all(checks[p] for p in direction)

    def perform(self, world: Any, actor: Any, a0: Any, direction: str, a1: Any) -> None:
        opposite = OPPOSITE_DIRECTIONS[direction]
        setattr(a0, direction, a1)
        setattr(a1, opposite, a0)

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, actor: Any, a0: Any, direction: str, a1: Any) -> None:
        if clause.truth_value:
            knowledge[a0].add(direction, a1, True, {clause})
            knowledge[a1].add(direction, a0, True, {clause})


class SetPos(Action):
    def is_valid(self, world: Any, actor: Any, a0: Any, x: Any, y: Any, z: Any = None) -> bool:
        return bool(actor and getattr(actor, "is_god", False) and a0 and x is not None and y is not None)

    def perform(self, world: Any, actor: Any, a0: Any, x: Any, y: Any, z: Any = None) -> None:
        a0.x, a0.y, a0.z = x, y, 0 if z is None else z

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, actor: Any, a0: Any, x: Any, y: Any, z: Any = None) -> None:
        knowledge[a0].set("x", x, True, {clause})
        knowledge[a0].set("y", y, True, {clause})
        knowledge[a0].set("z", 0 if z is None else z, True, {clause})


class Teleport(Action):
    def is_valid(self, world: Any, a0: Any, a1: Any) -> bool:
        if not (a0 and getattr(a0, "is_actor", False) and getattr(a0, "is_god", False)):
            return False
        if not (a1 and getattr(a1, "is_thing", False)) or a0.is_in == a1:
            return False
        return True

    def perform(self, world: Any, a0: Any, a1: Any) -> None:
        if getattr(a0, "is_in", None):
            a0.is_in.carry -= a0.size
        a0.is_in = a1
        a1.carry += a0.size

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, a0: Any, a1: Any) -> None:
        if clause.truth_value:
            knowledge[a0].set("is_in", a1, True, {clause})


class Give(Action):
    def is_valid(self, world: Any, actor: Any, obj: Any, recipient: Any) -> bool:
        if actor.is_in != recipient.is_in or actor == recipient:
            return False
        return obj.is_in == actor

    def perform(self, world: Any, actor: Any, obj: Any, recipient: Any) -> None:
        obj.is_in = recipient

    def update_knowledge(self, world: Any, knowledge: Any, clause: Any, actor: Any, obj: Any, recipient: Any) -> None:
        knowledge[obj].set("is_in", recipient, True, {clause})
        current = {}
        for entity in (actor, recipient, obj):
            current[entity] = list(knowledge[entity].values.get("is_in", []))
        knowledge[actor].merge("is_in", current[recipient], {clause})
        knowledge[recipient].merge("is_in", current[actor], {clause})


actions = {
    "get": Get(),
    "drop": Drop(),
    "give": Give(),
    "teleport": Teleport(),
    "create": Create(),
    "set": SetProperty(),
    "set_dir": SetDir(),
    "set_pos": SetPos(),
}

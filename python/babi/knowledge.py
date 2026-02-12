from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntityProperties:
    knowledge: "Knowledge"
    values: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def add(self, prop: str, value: Any, truth_value: bool, support: set[Any]) -> None:
        self.values.setdefault(prop, [])
        self.values[prop] = [
            item
            for item in self.values[prop]
            if not (
                item["value"] == value
                or (self.knowledge.exclusive.get(prop, False) and truth_value and item["truth_value"])
            )
        ]
        self.values[prop].append({"value": value, "truth_value": truth_value, "support": set(support)})

    def set(self, prop: str, value: Any, truth_value: bool, support: set[Any]) -> None:
        self.values[prop] = [{"value": value, "truth_value": truth_value, "support": set(support)}]

    def merge(self, prop: str, values: list[dict[str, Any]], support: set[Any]) -> None:
        self.rawadd(prop, values, support)
        true_values = [v for v in self.values[prop] if v["truth_value"]]
        if true_values:
            self.values[prop] = [true_values[0]]

    def rawset(self, prop: str, values: list[dict[str, Any]], support: set[Any] | None = None) -> None:
        copied = deepcopy(values)
        if support:
            for value in copied:
                value["support"] |= support
        self.values[prop] = copied

    def rawadd(self, prop: str, values: list[dict[str, Any]], support: set[Any] | None = None) -> None:
        self.values.setdefault(prop, [])
        copied = deepcopy(values)
        if support:
            for value in copied:
                value["support"] |= support
        self.values[prop].extend(copied)

    def is_true(self, prop: str, value: Any, return_support: bool = False):
        truth, support = False, set()
        for fact in self.values.get(prop, []):
            if fact["value"] == value and fact["truth_value"]:
                truth, support = True, fact["support"]
                break
        return (truth, support) if return_support else truth

    def is_false(self, prop: str, value: Any, return_support: bool = False):
        truth, support = False, set()
        for fact in self.values.get(prop, []):
            if fact["value"] == value and not fact["truth_value"]:
                truth, support = True, fact["support"]
            elif self.knowledge.exclusive.get(prop, False) and value != fact["value"] and fact["truth_value"]:
                truth, support = True, fact["support"]
        return (truth, support) if return_support else truth

    def get_truth_value(self, prop: str, value: Any, return_support: bool = False):
        is_true, s1 = self.is_true(prop, value, True)
        is_false, s2 = self.is_false(prop, value, True)
        support = s1 | s2
        if is_true or is_false:
            v = True if is_true else False
            return (v, support) if return_support else v
        return (None, support) if return_support else None

    def get_value(self, prop: str, return_support: bool = False):
        values, support = self.get_values(prop, True)
        if len(values) > 1:
            raise ValueError("this property has multiple values")
        if len(values) == 1:
            return (values[0], support[0]) if return_support else values[0]
        return (None, None) if return_support else None

    def get_values(self, prop: str, return_support: bool = False):
        vals, supports = [], []
        for value in self.values.get(prop, []):
            if self.is_true(prop, value["value"]):
                vals.append(value["value"])
                supports.append(value["support"])
        return (vals, supports) if return_support else vals

    def get_non_values(self, prop: str, return_support: bool = False):
        vals, supports = [], []
        for value in self.values.get(prop, []):
            if self.is_false(prop, value["value"]):
                vals.append(value["value"])
                supports.append(value["support"])
        return (vals, supports) if return_support else vals


class KnowledgeTable(dict):
    def __init__(self, knowledge: "Knowledge"):
        super().__init__()
        self.k = knowledge

    def __missing__(self, key: Any):
        if hasattr(key, "name"):
            val = EntityProperties(self.k)
            self[key] = val
            return val
        raise KeyError(f"Accessing unset key {key}")

    def find(self, prop: str, value: Any = None) -> list[Any]:
        matches = []
        for entity in self.keys():
            if hasattr(entity, "name"):
                entity_value = self[entity].get_value(prop)
                if entity_value and (value is None or entity_value == value):
                    matches.append(entity)
        return matches


class Knowledge:
    def __init__(self, world: Any, rules: list[Any] | None = None):
        self.t = 0
        self.knowledge: dict[int, KnowledgeTable] = {}
        self.world = world
        self.rules = rules or []
        self.story: dict[int, Any] = {}
        self.exclusive: dict[str, bool] = {}

    def get_value_history(self, entity: Any, prop: str, resolve_location: bool = True):
        value_history, support_history = [], []
        for t in range(1, self.t + 1):
            value, support = self.knowledge[t][entity].get_value(prop, True)
            if resolve_location and value is not None and getattr(value, "is_actor", False):
                value, new_support = self.knowledge[t][value].get_value(prop, True)
                if new_support:
                    support = (support or set()) | new_support
            if value and (not value_history or value_history[-1].name != value.name):
                value_history.append(value)
                support_history.append(support)
        return value_history, support_history

    def update(self, clause: Any) -> None:
        self.t += 1
        t = self.t
        self.story[t] = clause

        self.knowledge[t] = KnowledgeTable(self)
        if t > 1:
            for k, v in self.knowledge[t - 1].items():
                copied = EntityProperties(self)
                copied.values = deepcopy(v.values)
                self.knowledge[t][k] = copied

        if hasattr(clause, "is_applicable") and hasattr(clause, "perform") and hasattr(clause, "update_knowledge"):
            self.rules.append(clause)
        else:
            clause.action.update_knowledge(self.world, self.knowledge[t], clause, clause.actor, *clause.args)

        for rule in self.rules:
            if rule.is_applicable(clause, self.knowledge[t], self.story):
                rule.perform(self.world)
                rule.update_knowledge(self.world, self.knowledge[t], clause)

    def current(self) -> KnowledgeTable:
        return self.knowledge[self.t]

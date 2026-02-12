from __future__ import annotations

from pathlib import Path

from babi import Clause, Entity, Knowledge, World, actions
from babi.utilities import Grid, add_loc, split


def build_world() -> World:
    world = World()
    world.create_entity("john", {"is_actor": True, "is_thing": True, "size": 2, "is_gettable": False})
    world.create_entity("mary", {"is_actor": True, "is_thing": True, "size": 2, "is_gettable": False})
    world.create_entity("kitchen", {"is_location": True, "is_thing": True, "size": 10})
    world.create_entity("garden", {"is_location": True, "is_thing": True, "size": 10})
    world.create_entity("milk", {"is_gettable": True, "is_thing": True, "size": 1})
    return world


def test_entity_and_clause_perform() -> None:
    world = build_world()
    john = world.entities["john"]
    kitchen = world.entities["kitchen"]
    clause = Clause(world, True, world.god(), actions["set"], john, "is_in", kitchen)
    assert clause.is_valid()
    clause.perform()
    assert john.is_in is kitchen


def test_get_and_drop_actions_update_world() -> None:
    world = build_world()
    god = world.god()
    john = world.entities["john"]
    milk = world.entities["milk"]
    kitchen = world.entities["kitchen"]

    actions["set"].perform(world, god, john, "is_in", kitchen)
    actions["set"].perform(world, god, milk, "is_in", kitchen)

    assert actions["get"].is_valid(world, john, milk)
    actions["get"].perform(world, john, milk)
    assert milk.is_in is john

    assert actions["drop"].is_valid(world, john, milk)
    actions["drop"].perform(world, john, milk)
    assert milk.is_in is kitchen


def test_knowledge_truth_and_exclusive_inference() -> None:
    world = build_world()
    world.create_entity("hallway", {"is_location": True, "is_thing": True, "size": 10})
    knowledge = Knowledge(world)
    knowledge.exclusive["is_in"] = True

    john = world.entities["john"]
    kitchen = world.entities["kitchen"]
    garden = world.entities["garden"]

    clause = Clause(world, True, world.god(), actions["set"], john, "is_in", kitchen)
    knowledge.update(clause)

    assert knowledge.current()[john].is_true("is_in", kitchen)
    assert knowledge.current()[john].is_false("is_in", garden)


def test_world_load_and_command(tmp_path: Path) -> None:
    world = World()
    world.create_entity("john", {"is_actor": True, "is_thing": True, "size": 2})
    world.create_entity("kitchen", {"is_location": True, "is_thing": True, "size": 10})

    script = tmp_path / "world.txt"
    script.write_text("set john is_in kitchen\n", encoding="utf-8")
    world.load(str(script))

    assert world.entities["john"].is_in is world.entities["kitchen"]


def test_utilities_split_and_grid() -> None:
    assert split('john say "hello world"') == ["john", "say", "hello world"]

    grid = Grid(3)
    grid.add_node(1, "A")
    grid.add_node(2, "B")
    grid.add_node(3, "C")

    assert grid.dijkstra(1, 3) == [1, 2, 3]
    assert grid.manhattan(1, 3) == 2


def test_add_loc_sets_position_and_relations() -> None:
    world = World()
    world.create_entity("a", {"is_thing": True, "size": 1})
    world.create_entity("b", {"is_thing": True, "size": 1})
    grid = Grid(2)
    grid.add_node(1, world.entities["a"])
    grid.add_node(2, world.entities["b"])

    add_loc(grid, 1, world.entities["a"], world)
    add_loc(grid, 2, world.entities["b"], world)

    assert world.entities["a"].e is world.entities["b"]
    assert world.entities["b"].w is world.entities["a"]

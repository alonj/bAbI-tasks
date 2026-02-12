from __future__ import annotations

import heapq
import random
import shlex
from pathlib import Path
from typing import Any


DIRECTIONS = ["n", "s", "e", "w"]


def split(s: str) -> list[str]:
    return shlex.split(s)


def choice(a: list[Any] | set[Any], size: int = 1, replace: bool = False):
    is_set = isinstance(a, set)
    pool = list(a)
    if replace:
        picks = [random.choice(pool) for _ in range(size)]
    else:
        picks = random.sample(pool, size)
    return set(picks) if is_set else picks


class Grid:
    def __init__(self, width: int, height: int | None = None):
        self.width = width
        self.height = height or width
        self.nodes: dict[int, Any] = {}
        self.objects: dict[Any, int] = {}
        self.edges: dict[int, set[int]] = {i: set() for i in range(1, self.width * self.height + 1)}

    def to_coordinates(self, i: int) -> tuple[int, int]:
        return ((i - 1) % self.width + 1, (i - 1) // self.width + 1)

    def to_node(self, x: int, y: int) -> int:
        return x + (y - 1) * self.width

    def center(self) -> int:
        return (self.height // 2) * self.width + (self.width + 1) // 2

    def rel_node(self, i: int, direction: str) -> int | None:
        return {"n": i - self.width, "s": i + self.width, "e": i + 1, "w": i - 1}.get(direction)

    def add_node(self, i: int, obj: Any = None, edges: Any = None) -> None:
        self.nodes[i] = obj or True
        if obj is not None:
            self.objects[obj] = i
        for direction in DIRECTIONS:
            j = self.rel_node(i, direction)
            if j in self.nodes:
                self.add_edge(i, j)

    def remove_node(self, i: int):
        obj = self.nodes.pop(i)
        self.objects.pop(obj, None)
        edges = []
        for j in list(self.edges[i]):
            edges.append((i, j))
            self.remove_edge(i, j)
        return obj, edges

    def add_edge(self, i: int, j: int) -> None:
        self.edges[i].add(j)
        self.edges[j].add(i)

    def remove_edge(self, i: int, j: int) -> None:
        self.edges[i].discard(j)
        self.edges[j].discard(i)

    def manhattan(self, i: int, j: int, via: int | None = None) -> int:
        if via is not None:
            return self.manhattan(i, via) + self.manhattan(j, via)
        x1, y1 = self.to_coordinates(i)
        x2, y2 = self.to_coordinates(j)
        return abs(x1 - x2) + abs(y1 - y2)

    def yen(self, source: int, target: int, k: int):
        first = self.dijkstra(source, target)
        if not first:
            return []
        a = [first]
        b = []
        for _ in range(1, k):
            for i in range(len(a[-1]) - 1):
                spur_node = a[-1][i]
                root_path = a[-1][: i + 1]
                removed_edges = []
                removed_nodes = []

                for p in a:
                    if p[: i + 1] == root_path:
                        self.remove_edge(p[i], p[i + 1])
                        removed_edges.append((p[i], p[i + 1]))

                for node in root_path:
                    if node != spur_node:
                        removed_nodes.append((node, self.remove_node(node)))

                spur_path = self.dijkstra(spur_node, target)
                if spur_path:
                    b.append(root_path + spur_path[1:])

                for edge in removed_edges:
                    self.add_edge(*edge)
                for node, (obj, _edges) in removed_nodes:
                    self.add_node(node, obj)

            if not b:
                break
            b.sort(key=len)
            a.append(b.pop(0))
        return a

    def dijkstra(self, source: int, target: int):
        dist = {i: float("inf") for i in range(1, self.width * self.height + 1)}
        prev = {}
        dist[source] = 0
        pq = [(0, source)]

        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]:
                continue
            if u == target:
                break
            for v in self.edges[u]:
                nd = d + 1
                if nd < dist[v]:
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        if dist[target] == float("inf"):
            return None
        path = [target]
        u = target
        while u in prev:
            u = prev[u]
            path.append(u)
        return list(reversed(path))


def add_loc(grid: Grid, i: int, obj: Any, world: Any) -> None:
    world.perform_action("set_pos", world.god(), obj, *grid.to_coordinates(i))
    for direction in DIRECTIONS:
        j = grid.rel_node(i, direction)
        if j in grid.nodes:
            world.perform_action("set_dir", world.god(), obj, direction, grid.nodes[j])


def babi_home() -> Path:
    return Path(__file__).resolve().parents[1]

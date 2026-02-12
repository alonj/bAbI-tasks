from __future__ import annotations

from typing import Any


def stringify(story: list[Any], knowledge: Any, config: dict[str, Any] | None = None) -> str:
    """Minimal Python renderer.

    The Lua version ships a very extensive template engine; this Python port
    provides a compact symbolic renderer that keeps generated data usable.
    """

    lines = []
    for idx, item in enumerate(story, start=1):
        if hasattr(item, "truth_value") and hasattr(item, "actor") and hasattr(item, "action"):
            truth = "not " if not item.truth_value else ""
            args = " ".join(getattr(arg, "name", str(arg)) for arg in item.args)
            lines.append(f"{idx} {truth}{item.actor.name} {item.action} {args}".strip())
        elif hasattr(item, "kind"):
            args = getattr(item, "args", None)
            support = sorted(getattr(item, "support", []))
            lines.append(f"{idx} ? {item.kind} {args} {support}")
    return "\n".join(lines)

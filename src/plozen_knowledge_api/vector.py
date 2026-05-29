from __future__ import annotations

from collections.abc import Sequence


def vector_literal(values: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def uuid_array_literal(values: Sequence[str]) -> str:
    if not values:
        return "{}"
    return "{" + ",".join(values) + "}"

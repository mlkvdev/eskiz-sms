"""Pure protocol layer.

Each module describes one Eskiz resource as a set of plan factories — pure
functions that take typed arguments and return a :class:`RequestPlan` ready
for an executor to dispatch. No SDK semantics live here: no defaults, no
config lookup, no logging. That keeps protocol logic trivially unit-testable
without HTTP and keeps the SDK's UX layer (the resources) free to evolve
without touching wire format.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from eskiz.transport.base import RawResponse

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RequestPlan(Generic[T]):
    """Self-contained description of one HTTP call plus its parser."""

    method: str
    path: str
    parse: Callable[[RawResponse], T]
    data: dict[str, Any] | None = None
    json: Any = None
    params: dict[str, Any] | None = None


__all__ = ["RequestPlan"]

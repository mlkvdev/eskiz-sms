"""Pluggable token storage.

A token storage is anything with ``get`` / ``set`` / ``clear``. The SDK ships
an in-memory backend; users wanting persistence (Redis, file, dotenv) provide
their own implementation conforming to :class:`TokenStorage`.
"""

from __future__ import annotations

import threading
from typing import Protocol


class TokenStorage(Protocol):
    """Protocol implemented by every token storage backend."""

    def get(self) -> str | None:
        """Return the stored token, or ``None`` if there is none."""
        ...

    def set(self, token: str) -> None:
        """Persist ``token``."""
        ...

    def clear(self) -> None:
        """Remove the stored token, if any."""
        ...


class MemoryTokenStorage:
    """In-memory token storage. Thread-safe, process-local."""

    __slots__ = ("_lock", "_token")

    def __init__(self, initial: str | None = None) -> None:
        self._token = initial
        self._lock = threading.Lock()

    def get(self) -> str | None:
        with self._lock:
            return self._token

    def set(self, token: str) -> None:
        with self._lock:
            self._token = token

    def clear(self) -> None:
        with self._lock:
            self._token = None

"""Internal SDK configuration.

A single immutable :class:`Config` carries every knob the transport, auth,
and client layers need. It is *not* part of the public API — users pass
the same fields as kwargs to :class:`eskiz.EskizSMS` /
:class:`eskiz.AsyncEskizSMS`, which build the config object internally.
The class is reachable via ``from eskiz.config import Config`` for advanced
users who want to share one configuration across multiple clients, but it
is intentionally absent from ``eskiz.__all__``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eskiz.auth.storage import TokenStorage

DEFAULT_BASE_URL = "https://notify.eskiz.uz/api"
DEFAULT_TIMEOUT = 10.0
DEFAULT_FROM_WHOM = "4546"


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable internal configuration. See client docstrings for fields."""

    email: str
    password: str = field(repr=False)
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    callback_url: str | None = None
    from_whom: str = DEFAULT_FROM_WHOM
    token_storage: TokenStorage | None = None
    enable_token_refresh: bool = True
    max_retries: int = 0
    allow_insecure_callback: bool = False
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("eskiz"))

"""Top-level SDK configuration.

A single immutable :class:`Config` carries every knob the transport, auth, and
client layers need. Replaces the ad-hoc kwargs-on-the-client pattern from
v0.x — adding a new option is one line here, not a signature change.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eskiz.auth.storage import TokenStorage

DEFAULT_BASE_URL = "https://notify.eskiz.uz/api"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_TOKEN_REFRESH_RETRIES = 1


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable configuration passed to clients.

    Attributes:
        email: Eskiz account email.
        password: Eskiz account password.
        base_url: API base URL. Override only for staging or proxies.
        timeout: Per-request timeout in seconds.
        callback_url: Default callback URL for SMS delivery webhooks.
        token_storage: Backend used to persist the bearer token. Defaults to
            in-memory storage created lazily by the client if ``None``.
        max_token_refresh_retries: Number of times to retry a 401 by
            refreshing the token. ``1`` is safe; higher values mask bugs.
        logger: Logger to emit debug/info/warning messages on. The SDK
            redacts secrets before logging.
    """

    email: str
    password: str = field(repr=False)
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    callback_url: str | None = None
    token_storage: TokenStorage | None = None
    max_token_refresh_retries: int = DEFAULT_MAX_TOKEN_REFRESH_RETRIES
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("eskiz"))

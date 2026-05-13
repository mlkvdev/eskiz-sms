"""Shared transport types and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from eskiz.exceptions import (
    EskizBadRequest,
    EskizHTTPError,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
)


@dataclass(slots=True)
class RawResponse:
    """Lightweight wrapper around the parsed HTTP response."""

    status_code: int
    data: dict[str, Any] | list[Any] | str
    headers: httpx.Headers


_INVALID_CREDENTIALS_MESSAGES = frozenset({"Invalid credentials", "invalid_credentials"})
_TOKEN_INVALID_STATUSES = frozenset({"token_invalid"})

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
"""HTTP methods that the SDK retries on 5xx / read timeout.

POST/PATCH/DELETE are excluded because their request body may have been
processed even when the server failed to respond. The httpx transport's
``retries=`` knob still handles pre-request connection errors for those.
"""

_RETRY_BASE_DELAY = 0.2
_RETRY_MAX_DELAY = 5.0


def retry_delay(attempt: int) -> float:
    """Exponential backoff: 0.2, 0.4, 0.8, ... capped at 5s."""
    return min(_RETRY_BASE_DELAY * (2**attempt), _RETRY_MAX_DELAY)


def parse_httpx(response: httpx.Response) -> RawResponse:
    """Convert an :class:`httpx.Response` to a :class:`RawResponse`.

    Tolerates JSON, text, and CSV bodies; never raises on parse failure.
    Tries JSON first regardless of content-type so misconfigured servers
    (``text/json``, missing header, etc.) still parse correctly.
    """
    data: dict[str, Any] | list[Any] | str
    try:
        data = response.json()
    except ValueError:
        data = response.text
    return RawResponse(status_code=response.status_code, data=data, headers=response.headers)


def is_token_expired(response: RawResponse) -> bool:
    """Return True if a 401 should trigger a token refresh.

    Any 401 is treated as expiry-eligible *except* when the server
    explicitly marks the token as invalid (revoked / malformed) — refresh
    won't help there, so we surface the error instead.
    """
    if response.status_code != 401:
        return False
    return not (
        isinstance(response.data, dict) and response.data.get("status") in _TOKEN_INVALID_STATUSES
    )


def raise_for_response(response: RawResponse) -> None:
    """Raise the appropriate :class:`EskizError` subclass for a non-2xx response."""
    if 200 <= response.status_code < 300:
        return

    message: str
    status: str | int | None
    if isinstance(response.data, dict):
        raw_message = response.data.get("message")
        message = str(raw_message) if raw_message is not None else f"HTTP {response.status_code}"
        status = response.data.get("status")
    else:
        message = (
            response.data if isinstance(response.data, str) else f"HTTP {response.status_code}"
        )
        status = None

    if (
        response.status_code == 401
        and message in _INVALID_CREDENTIALS_MESSAGES
    ):
        raise InvalidCredentials(message, status=status, status_code=response.status_code)
    if status in _TOKEN_INVALID_STATUSES:
        raise TokenInvalid(message, status=status, status_code=response.status_code)
    if response.status_code == 401:
        raise TokenExpired(message, status=status, status_code=response.status_code)
    raise EskizBadRequest(message, status=status, status_code=response.status_code)


def wrap_httpx_error(exc: httpx.HTTPError) -> EskizHTTPError:
    """Translate an httpx transport error to :class:`EskizHTTPError`."""
    return EskizHTTPError(str(exc) or exc.__class__.__name__)

"""Shared transport types and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from eskiz.exceptions import (
    BadRequest,
    HTTPError,
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


def parse_httpx(response: httpx.Response) -> RawResponse:
    """Convert an :class:`httpx.Response` to a :class:`RawResponse`.

    Tolerates JSON, text, and CSV bodies; never raises on parse failure.
    """
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
    data: dict[str, Any] | list[Any] | str
    if content_type == "application/json":
        try:
            data = response.json()
        except ValueError:
            data = response.text
    else:
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

    if message in _INVALID_CREDENTIALS_MESSAGES:
        raise InvalidCredentials(message, status=status, status_code=response.status_code)
    if status in _TOKEN_INVALID_STATUSES:
        raise TokenInvalid(message, status=status, status_code=response.status_code)
    if response.status_code == 401:
        raise TokenExpired(message, status=status, status_code=response.status_code)
    raise BadRequest(message, status=status, status_code=response.status_code)


def wrap_httpx_error(exc: httpx.HTTPError) -> HTTPError:
    """Translate an httpx transport error to :class:`HTTPError`."""
    return HTTPError(str(exc) or exc.__class__.__name__)

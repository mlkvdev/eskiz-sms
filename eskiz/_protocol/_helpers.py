"""Helpers shared by protocol modules — payload shaping and parsing primitives."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from eskiz._validators import normalize_phone, validate_callback_url
from eskiz.exceptions import EskizBadRequest, EskizValidationError
from eskiz.models import BatchMessage
from eskiz.transport.base import RawResponse

T = TypeVar("T")

_MAX_ERROR_PAYLOAD = 200


def datetime_str(value: datetime | str) -> str:
    """Format a datetime to Eskiz's ``YYYY-MM-DD HH:MM`` shape."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return value


def _truncate(payload: Any) -> str:
    snippet = repr(payload)
    if len(snippet) > _MAX_ERROR_PAYLOAD:
        snippet = snippet[:_MAX_ERROR_PAYLOAD] + "..."
    return snippet


def unexpected_shape(payload: Any, *, status_code: int | None = None) -> EskizBadRequest:
    """Build an :class:`EskizBadRequest` describing an unparseable response."""
    return EskizBadRequest(
        f"Unexpected response shape: {_truncate(payload)}", status_code=status_code
    )


def envelope_data(payload: Any) -> Any:
    """Pull ``data`` out of an envelope or raise :class:`EskizBadRequest`."""
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    raise EskizBadRequest(f"Unexpected response shape: {_truncate(payload)}")


def extract_token(response: RawResponse) -> str:
    """Pull the bearer token out of an auth/login or auth/refresh response."""
    payload = response.data
    if not isinstance(payload, dict):
        raise EskizBadRequest("Unexpected auth response", status_code=response.status_code)
    data = payload.get("data")
    if not isinstance(data, dict) or "token" not in data:
        raise EskizBadRequest("Auth response missing token", status_code=response.status_code)
    token = data["token"]
    if not isinstance(token, str):
        raise EskizBadRequest(
            "Auth response token is not a string", status_code=response.status_code
        )
    return token


def bool_flag(value: bool | None) -> str | None:
    """Convert an optional bool to Eskiz's ``"1"``/``"0"`` form-field convention."""
    if value is None:
        return None
    return "1" if value else "0"


def apply_callback(
    body: dict[str, Any],
    callback_url: str | None,
    *,
    allow_insecure: bool = False,
) -> None:
    """Validate and inject a ``callback_url`` into a form body in place."""
    if callback_url is not None:
        body["callback_url"] = validate_callback_url(callback_url, allow_insecure=allow_insecure)


def normalize_batch_messages(
    messages: list[BatchMessage] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize batch message rows: phone digits-only, BatchMessage → dict."""
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, BatchMessage):
            out.append(m.model_dump())
        else:
            if "to" not in m:
                raise EskizValidationError("Batch message missing required 'to' field")
            out.append({**m, "to": normalize_phone(str(m["to"]))})
    return out


def envelope_list_parser(item: Callable[[Any], T]) -> Callable[[RawResponse], list[T]]:
    """Build a parser that maps an enveloped ``{data: [...]}`` to ``list[T]``."""

    def parse(r: RawResponse) -> list[T]:
        rows = envelope_data(r.data)
        if not isinstance(rows, list):
            raise unexpected_shape(rows, status_code=r.status_code)
        return [item(row) for row in rows]

    return parse

"""Helpers shared by protocol modules — payload shaping and parsing primitives."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from eskiz._validators import normalize_phone, validate_callback_url
from eskiz.exceptions import BadRequest
from eskiz.models import BatchMessage
from eskiz.transport.base import RawResponse

T = TypeVar("T")

_MAX_ERROR_PAYLOAD = 200


def datetime_str(value: datetime | str) -> str:
    """Format a datetime to Eskiz's ``YYYY-MM-DD HH:MM`` shape."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return value


def envelope_data(payload: Any) -> Any:
    """Pull ``data`` out of an envelope or raise :class:`BadRequest`."""
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    snippet = repr(payload)
    if len(snippet) > _MAX_ERROR_PAYLOAD:
        snippet = snippet[:_MAX_ERROR_PAYLOAD] + "..."
    raise BadRequest(f"Unexpected response shape: {snippet}")


def extract_token(response: RawResponse) -> str:
    """Pull the bearer token out of an auth/login or auth/refresh response."""
    payload = response.data
    if not isinstance(payload, dict):
        raise BadRequest("Unexpected auth response", status_code=response.status_code)
    data = payload.get("data")
    if not isinstance(data, dict) or "token" not in data:
        raise BadRequest("Auth response missing token", status_code=response.status_code)
    return str(data["token"])


def bool_flag(value: bool | None) -> str | None:
    """Convert an optional bool to Eskiz's ``"1"``/``"0"`` form-field convention."""
    if value is None:
        return None
    return "1" if value else "0"


def apply_callback(body: dict[str, Any], callback_url: str | None) -> None:
    """Validate and inject a ``callback_url`` into a form body in place."""
    if callback_url is not None:
        body["callback_url"] = validate_callback_url(callback_url)


def normalize_batch_messages(
    messages: list[BatchMessage] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize batch message rows: phone digits-only, BatchMessage → dict."""
    out: list[dict[str, Any]] = []
    for m in messages:
        if isinstance(m, BatchMessage):
            out.append(m.model_dump())
        else:
            out.append({**m, "to": normalize_phone(str(m["to"]))})
    return out


def envelope_list_parser(item: Callable[[Any], T]) -> Callable[[RawResponse], list[T]]:
    """Build a parser that maps an enveloped ``{data: [...]}`` to ``list[T]``."""

    def parse(r: RawResponse) -> list[T]:
        rows = envelope_data(r.data)
        if not isinstance(rows, list):
            return []
        return [item(row) for row in rows]

    return parse

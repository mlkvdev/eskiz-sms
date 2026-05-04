"""Input validators kept in one place for reuse."""

from __future__ import annotations

from urllib.parse import urlparse

from eskiz.exceptions import ValidationError


def validate_callback_url(url: str) -> str:
    """Return ``url`` if it parses as a valid http(s) URL; raise otherwise."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"Invalid callback URL: {url!r}")
    return url


def normalize_phone(value: str) -> str:
    """Normalize a phone number: strip ``+``, spaces, dashes."""
    return value.replace("+", "").replace(" ", "").replace("-", "")

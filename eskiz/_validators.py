"""Input validators kept in one place for reuse."""

from __future__ import annotations

from urllib.parse import urlparse

from eskiz.exceptions import EskizValidationError


def validate_callback_url(url: str, *, allow_insecure: bool = False) -> str:
    """Return ``url`` if it parses as a valid HTTPS URL; raise otherwise.

    Plain ``http://`` is rejected by default — Eskiz's webhooks carry the
    recipient's phone number and message status, neither of which should
    cross the wire in cleartext. Pass ``allow_insecure=True`` to opt back
    into ``http://`` for staging or local testing.
    """
    parsed = urlparse(url)
    if not parsed.netloc:
        raise EskizValidationError(f"Invalid callback URL: {url!r}")
    allowed = {"https", "http"} if allow_insecure else {"https"}
    if parsed.scheme not in allowed:
        raise EskizValidationError(
            f"Invalid callback URL scheme {parsed.scheme!r}: "
            f"expected https (pass allow_insecure=True to permit http)"
        )
    return url


def normalize_phone(value: str) -> str:
    """Normalize a phone number: strip ``+``, spaces, dashes."""
    return value.replace("+", "").replace(" ", "").replace("-", "")

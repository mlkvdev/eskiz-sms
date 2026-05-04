"""Exception hierarchy for the Eskiz SDK.

All SDK errors derive from :class:`EskizError`. Network and protocol issues
become :class:`HTTPError`; auth issues become :class:`AuthError` (with
:class:`InvalidCredentials`, :class:`TokenExpired`, :class:`TokenInvalid` as
subclasses); API-side rejections become :class:`BadRequest`. Local input
validation surfaces as :class:`ValidationError`.
"""

from __future__ import annotations


class EskizError(Exception):
    """Base class for every error raised by the SDK."""

    def __init__(
        self,
        message: str,
        *,
        status: str | int | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.status_code = status_code

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"http={self.status_code}")
        if self.status is not None:
            parts.append(f"status={self.status}")
        return " ".join(parts)


class HTTPError(EskizError):
    """Network, TLS, or transport-layer failure."""


class AuthError(EskizError):
    """Authentication / authorization failure."""


class InvalidCredentials(AuthError):
    """Login rejected — email or password is wrong."""


class TokenExpired(AuthError):
    """Token has expired and could not be refreshed."""


class TokenInvalid(AuthError):
    """Token is rejected by the server (revoked, malformed, etc.)."""


class BadRequest(EskizError):
    """Server returned a non-success status with an error payload."""


class ValidationError(EskizError):
    """Local input failed validation before the request was sent."""

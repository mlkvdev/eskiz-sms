"""Exception hierarchy for the Eskiz SDK.

All SDK errors derive from :class:`EskizError`. Network and protocol issues
become :class:`EskizHTTPError`; auth issues become :class:`AuthError` (with
:class:`InvalidCredentials`, :class:`TokenExpired`, :class:`TokenInvalid` as
subclasses); API-side rejections become :class:`EskizBadRequest`. Local
input validation surfaces as :class:`EskizValidationError`.
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
        parts = [f"{type(self).__name__}: {self.message}"]
        if self.status_code is not None:
            parts.append(f"http={self.status_code}")
        if self.status is not None:
            parts.append(f"status={self.status}")
        return " ".join(parts)


class EskizHTTPError(EskizError):
    """Network, TLS, or transport-layer failure."""


class AuthError(EskizError):
    """Authentication / authorization failure."""


class InvalidCredentials(AuthError):
    """Login rejected — email or password is wrong."""


class TokenExpired(AuthError):
    """Token has expired and could not be refreshed."""


class TokenInvalid(AuthError):
    """Token is rejected by the server (revoked, malformed, etc.)."""


class EskizBadRequest(EskizError):
    """Server returned a non-success status with an error payload."""


class EskizValidationError(EskizError):
    """Local input failed validation before the request was sent."""

"""Eskiz SMS — modern Python SDK for the Eskiz.uz SMS gateway."""

from importlib.metadata import PackageNotFoundError, version

from eskiz.aio import AsyncEskizSMS
from eskiz.auth.backends import DotenvTokenStorage
from eskiz.auth.storage import MemoryTokenStorage, TokenStorage
from eskiz.client import EskizSMS
from eskiz.exceptions import (
    AuthError,
    EskizBadRequest,
    EskizError,
    EskizHTTPError,
    EskizValidationError,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
)

try:
    __version__ = version("eskiz-sms")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "AsyncEskizSMS",
    "AuthError",
    "DotenvTokenStorage",
    "EskizBadRequest",
    "EskizError",
    "EskizHTTPError",
    "EskizSMS",
    "EskizValidationError",
    "InvalidCredentials",
    "MemoryTokenStorage",
    "TokenExpired",
    "TokenInvalid",
    "TokenStorage",
    "__version__",
]

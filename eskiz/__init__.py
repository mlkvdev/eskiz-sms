"""Eskiz SMS — modern Python SDK for the Eskiz.uz SMS gateway."""

from importlib.metadata import PackageNotFoundError, version

from eskiz.aio import AsyncEskizSMS
from eskiz.auth.backends import DotenvTokenStorage
from eskiz.auth.storage import MemoryTokenStorage, TokenStorage
from eskiz.client import EskizSMS
from eskiz.config import Config
from eskiz.exceptions import (
    AuthError,
    BadRequest,
    EskizError,
    HTTPError,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
    ValidationError,
)

try:
    __version__ = version("eskiz-sms")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "AsyncEskizSMS",
    "AuthError",
    "BadRequest",
    "Config",
    "DotenvTokenStorage",
    "EskizError",
    "EskizSMS",
    "HTTPError",
    "InvalidCredentials",
    "MemoryTokenStorage",
    "TokenExpired",
    "TokenInvalid",
    "TokenStorage",
    "ValidationError",
    "__version__",
]

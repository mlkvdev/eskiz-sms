"""Sync facade — :class:`EskizSMS`.

The client is composition only: it owns the transport, token manager, and
executor, and exposes resources as attributes. All endpoint logic lives in
:mod:`eskiz._protocol` (wire format) and :mod:`eskiz.resources` (SDK
semantics).
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

from eskiz._protocol import auth as _auth_proto
from eskiz.auth.storage import MemoryTokenStorage
from eskiz.auth.token import SyncTokenManager
from eskiz.config import Config
from eskiz.exceptions import InvalidCredentials, TokenExpired
from eskiz.resources import (
    AuthResource,
    ReportsResource,
    SmsResource,
    TemplatesResource,
)
from eskiz.resources._base import SyncExecutor
from eskiz.transport.sync import SyncTransport


def _login(executor: SyncExecutor, email: str, password: str) -> str:
    """Run a login and re-raise generic 401s as :class:`InvalidCredentials`."""
    try:
        return executor.run_unauth(_auth_proto.login(email, password))
    except TokenExpired as exc:
        raise InvalidCredentials(
            exc.message, status=exc.status, status_code=exc.status_code
        ) from exc


class EskizSMS:
    """Synchronous client for the Eskiz SMS gateway."""

    __slots__ = (
        "_config",
        "_executor",
        "_tokens",
        "_transport",
        "auth",
        "reports",
        "sms",
        "templates",
    )

    def __init__(self, config: Config) -> None:
        self._config = config
        self._transport = SyncTransport(config)
        self._executor = SyncExecutor(self._transport)

        storage = config.token_storage or MemoryTokenStorage()
        self._tokens = SyncTokenManager(
            email=config.email,
            password=config.password,
            storage=storage,
            login_fn=lambda email, pw: _login(self._executor, email, pw),
            refresh_fn=lambda token: self._executor.run_with_token(_auth_proto.refresh(), token),
        )
        self._transport.attach_token_manager(self._tokens)

        self.auth: AuthResource = AuthResource(self._executor, config)
        self.sms: SmsResource = SmsResource(self._executor, config)
        self.templates: TemplatesResource = TemplatesResource(self._executor, config)
        self.reports: ReportsResource = ReportsResource(self._executor, config)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

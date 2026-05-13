"""Sync facade — :class:`EskizSMS`.

The client is composition only: it owns the transport, token manager, and
executor, and exposes resources as attributes. All endpoint logic lives in
:mod:`eskiz._protocol` (wire format) and :mod:`eskiz.resources` (SDK
semantics).
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import TYPE_CHECKING, Self

from eskiz._protocol import auth as _auth_proto
from eskiz.auth.storage import MemoryTokenStorage
from eskiz.auth.token import SyncTokenManager
from eskiz.config import DEFAULT_BASE_URL, DEFAULT_FROM_WHOM, DEFAULT_TIMEOUT, Config
from eskiz.exceptions import InvalidCredentials, TokenExpired
from eskiz.resources import (
    AuthResource,
    ReportsResource,
    SmsResource,
    TemplatesResource,
)
from eskiz.resources._base import SyncExecutor
from eskiz.transport.sync import SyncTransport

if TYPE_CHECKING:
    from eskiz.auth.storage import TokenStorage


def _login(executor: SyncExecutor, email: str, password: str) -> str:
    """Run a login and re-raise generic 401s as :class:`InvalidCredentials`."""
    try:
        return executor.run_unauth(_auth_proto.login(email, password))
    except TokenExpired as exc:
        raise InvalidCredentials(
            exc.message, status=exc.status, status_code=exc.status_code
        ) from exc


class EskizSMS:
    """Synchronous client for the Eskiz SMS gateway.

    Args:
        email: Eskiz account email.
        password: Eskiz account password.
        base_url: API base URL. Override only for staging or proxies.
        timeout: Per-request timeout in seconds.
        callback_url: Default callback URL for SMS delivery webhooks.
        from_whom: Default alphanumeric sender id used by ``sms.send`` and
            ``sms.send_batch`` when the caller doesn't pass one.
        token_storage: Backend used to persist the bearer token. Defaults to
            in-memory storage if not given.
        enable_token_refresh: When ``True`` (the default) a 401 triggers a
            single ``PATCH /auth/refresh`` retry, falling back to fresh
            login if refresh itself fails. Set to ``False`` to surface 401s
            immediately as :class:`TokenExpired`.
        logger: Logger used for refresh/retry/auth events. The SDK never
            logs tokens or passwords.
    """

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

    def __init__(
        self,
        *,
        email: str,
        password: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        callback_url: str | None = None,
        from_whom: str = DEFAULT_FROM_WHOM,
        token_storage: TokenStorage | None = None,
        enable_token_refresh: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        config = Config(
            email=email,
            password=password,
            base_url=base_url,
            timeout=timeout,
            callback_url=callback_url,
            from_whom=from_whom,
            token_storage=token_storage,
            enable_token_refresh=enable_token_refresh,
            logger=logger if logger is not None else logging.getLogger("eskiz"),
        )
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
            logger=config.logger,
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

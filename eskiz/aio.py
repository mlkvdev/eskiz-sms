"""Async facade — :class:`AsyncEskizSMS`. Composes async resources."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import TYPE_CHECKING, Self

from eskiz._protocol import auth as _auth_proto
from eskiz.auth.storage import MemoryTokenStorage
from eskiz.auth.token import AsyncTokenManager
from eskiz.config import DEFAULT_BASE_URL, DEFAULT_FROM_WHOM, DEFAULT_TIMEOUT, Config
from eskiz.exceptions import InvalidCredentials, TokenExpired
from eskiz.resources import (
    AsyncAuthResource,
    AsyncReportsResource,
    AsyncSmsResource,
    AsyncTemplatesResource,
)
from eskiz.resources._base import AsyncExecutor
from eskiz.transport.aio import AsyncTransport

if TYPE_CHECKING:
    from eskiz.auth.storage import TokenStorage


async def _login(executor: AsyncExecutor, email: str, password: str) -> str:
    """Run a login and re-raise generic 401s as :class:`InvalidCredentials`."""
    try:
        return await executor.run_unauth(_auth_proto.login(email, password))
    except TokenExpired as exc:
        raise InvalidCredentials(
            exc.message, status=exc.status, status_code=exc.status_code
        ) from exc


class AsyncEskizSMS:
    """Asynchronous client for the Eskiz SMS gateway. See :class:`EskizSMS` for argument docs."""

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
        self._transport = AsyncTransport(config)
        self._executor = AsyncExecutor(self._transport)

        storage = config.token_storage or MemoryTokenStorage()
        self._tokens = AsyncTokenManager(
            email=config.email,
            password=config.password,
            storage=storage,
            login_fn=lambda email, pw: _login(self._executor, email, pw),
            refresh_fn=lambda token: self._executor.run_with_token(_auth_proto.refresh(), token),
            logger=config.logger,
        )
        self._transport.attach_token_manager(self._tokens)

        self.auth: AsyncAuthResource = AsyncAuthResource(self._executor, config)
        self.sms: AsyncSmsResource = AsyncSmsResource(self._executor, config)
        self.templates: AsyncTemplatesResource = AsyncTemplatesResource(self._executor, config)
        self.reports: AsyncReportsResource = AsyncReportsResource(self._executor, config)

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

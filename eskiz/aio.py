"""Async facade — :class:`AsyncEskizSMS`. Composes async resources."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from eskiz._protocol import auth as _auth_proto
from eskiz.auth.storage import MemoryTokenStorage
from eskiz.auth.token import AsyncTokenManager
from eskiz.config import Config
from eskiz.exceptions import InvalidCredentials, TokenExpired
from eskiz.resources import (
    AsyncAuthResource,
    AsyncReportsResource,
    AsyncSmsResource,
    AsyncTemplatesResource,
)
from eskiz.resources._base import AsyncExecutor
from eskiz.transport.aio import AsyncTransport


async def _login(executor: AsyncExecutor, email: str, password: str) -> str:
    """Run a login and re-raise generic 401s as :class:`InvalidCredentials`."""
    try:
        return await executor.run_unauth(_auth_proto.login(email, password))
    except TokenExpired as exc:
        raise InvalidCredentials(
            exc.message, status=exc.status, status_code=exc.status_code
        ) from exc


class AsyncEskizSMS:
    """Asynchronous client for the Eskiz SMS gateway."""

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
        self._transport = AsyncTransport(config)
        self._executor = AsyncExecutor(self._transport)

        storage = config.token_storage or MemoryTokenStorage()
        self._tokens = AsyncTokenManager(
            email=config.email,
            password=config.password,
            storage=storage,
            login_fn=lambda email, pw: _login(self._executor, email, pw),
            refresh_fn=lambda token: self._executor.run_with_token(_auth_proto.refresh(), token),
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

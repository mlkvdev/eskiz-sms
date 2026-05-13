"""Async HTTP transport — owns one :class:`httpx.AsyncClient`."""

from __future__ import annotations

import asyncio
from types import TracebackType
from typing import TYPE_CHECKING, Any, Self

import httpx

from eskiz.config import Config
from eskiz.exceptions import TokenInvalid
from eskiz.transport.base import (
    SAFE_METHODS,
    RawResponse,
    is_token_expired,
    parse_httpx,
    raise_for_response,
    retry_delay,
    wrap_httpx_error,
)

if TYPE_CHECKING:
    from eskiz.auth.token import AsyncTokenManager


class AsyncTransport:
    """Owns the :class:`httpx.AsyncClient`."""

    __slots__ = ("_client", "_config", "_token_manager")

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            transport=httpx.AsyncHTTPTransport(retries=max(config.max_retries, 0)),
        )
        self._token_manager: AsyncTokenManager | None = None

    def attach_token_manager(self, manager: AsyncTokenManager) -> None:
        self._token_manager = manager

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        """Issue one HTTP call. See :class:`SyncTransport.request_raw` for retry semantics."""
        headers = {"Authorization": f"Bearer {token}"} if token else None
        max_attempts = (
            self._config.max_retries + 1 if method.upper() in SAFE_METHODS else 1
        )
        for attempt in range(max_attempts):
            is_last = attempt == max_attempts - 1
            try:
                response = await self._client.request(
                    method, path, data=data, json=json, params=params, headers=headers
                )
            except (httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                if is_last:
                    self._config.logger.debug("eskiz http error: %s %s: %s", method, path, exc)
                    raise wrap_httpx_error(exc) from exc
                self._config.logger.debug(
                    "eskiz retry %d/%d: %s %s: %s",
                    attempt + 1, max_attempts - 1, method, path, exc,
                )
                await asyncio.sleep(retry_delay(attempt))
                continue
            except httpx.HTTPError as exc:
                self._config.logger.debug("eskiz http error: %s %s: %s", method, path, exc)
                raise wrap_httpx_error(exc) from exc

            if 500 <= response.status_code < 600 and not is_last:
                self._config.logger.debug(
                    "eskiz retry %d/%d after HTTP %d: %s %s",
                    attempt + 1, max_attempts - 1, response.status_code, method, path,
                )
                await asyncio.sleep(retry_delay(attempt))
                continue
            return parse_httpx(response)
        raise RuntimeError("retry loop exhausted")  # pragma: no cover

    async def request_unauth(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        parsed = await self.request_raw(method, path, data=data, json=json, params=params)
        raise_for_response(parsed)
        return parsed

    async def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        if self._token_manager is None:
            raise RuntimeError("Token manager not attached")
        token = await self._token_manager.get()
        parsed = await self.request_raw(
            method, path, token=token, data=data, json=json, params=params
        )
        if is_token_expired(parsed) and self._config.enable_token_refresh:
            self._config.logger.debug("eskiz 401 on %s %s; refreshing token", method, path)
            token = await self._token_manager.refresh_after_failure(token)
            parsed = await self.request_raw(
                method, path, token=token, data=data, json=json, params=params
            )
            if is_token_expired(parsed):
                raise TokenInvalid(
                    "Token refresh produced a token that was rejected on retry",
                    status_code=parsed.status_code,
                )
        raise_for_response(parsed)
        return parsed

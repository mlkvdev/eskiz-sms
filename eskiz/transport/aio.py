"""Async HTTP transport — owns one :class:`httpx.AsyncClient`."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx

from eskiz.config import Config
from eskiz.exceptions import TokenInvalid
from eskiz.transport.base import (
    RawResponse,
    is_token_expired,
    parse_httpx,
    raise_for_response,
    wrap_httpx_error,
)


class AsyncTransport:
    """Owns the :class:`httpx.AsyncClient`."""

    __slots__ = ("_client", "_config", "_token_manager")

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=config.timeout)
        self._token_manager: Any | None = None

    def attach_token_manager(self, manager: Any) -> None:
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
        headers = {"Authorization": f"Bearer {token}"} if token else None
        try:
            response = await self._client.request(
                method, path, data=data, json=json, params=params, headers=headers
            )
        except httpx.HTTPError as exc:
            raise wrap_httpx_error(exc) from exc
        return parse_httpx(response)

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
        if is_token_expired(parsed) and self._config.max_token_refresh_retries > 0:
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

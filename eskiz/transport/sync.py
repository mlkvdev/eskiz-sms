"""Sync HTTP transport — owns one :class:`httpx.Client`."""

from __future__ import annotations

import time
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
    from eskiz.auth.token import SyncTokenManager


class SyncTransport:
    """Owns the :class:`httpx.Client` and performs requests."""

    __slots__ = ("_client", "_config", "_token_manager")

    def __init__(self, config: Config) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            transport=httpx.HTTPTransport(retries=max(config.max_retries, 0)),
        )
        self._token_manager: SyncTokenManager | None = None

    def attach_token_manager(self, manager: SyncTokenManager) -> None:
        self._token_manager = manager

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # ----- requests -----

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        """Issue a single HTTP call without auth-retry semantics.

        For safe methods (GET/HEAD/OPTIONS) a read timeout or 5xx response
        is retried up to ``config.max_retries`` times with exponential
        backoff. Unsafe methods (POST/PATCH/DELETE) are never retried here
        — only at the httpx transport layer, which retries pre-request
        connection errors so no request body is sent twice.
        """
        headers = {"Authorization": f"Bearer {token}"} if token else None
        max_attempts = (
            self._config.max_retries + 1 if method.upper() in SAFE_METHODS else 1
        )
        for attempt in range(max_attempts):
            is_last = attempt == max_attempts - 1
            try:
                response = self._client.request(
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
                time.sleep(retry_delay(attempt))
                continue
            except httpx.HTTPError as exc:
                self._config.logger.debug("eskiz http error: %s %s: %s", method, path, exc)
                raise wrap_httpx_error(exc) from exc

            if 500 <= response.status_code < 600 and not is_last:
                self._config.logger.debug(
                    "eskiz retry %d/%d after HTTP %d: %s %s",
                    attempt + 1, max_attempts - 1, response.status_code, method, path,
                )
                time.sleep(retry_delay(attempt))
                continue
            return parse_httpx(response)
        # Unreachable: the loop either returns or raises on each iteration.
        raise RuntimeError("retry loop exhausted")  # pragma: no cover

    def request_unauth(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        """Unauthenticated request (login). Raises on non-2xx."""
        parsed = self.request_raw(method, path, data=data, json=json, params=params)
        raise_for_response(parsed)
        return parsed

    def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> RawResponse:
        """Authenticated request. Refreshes token on 401 and retries once."""
        if self._token_manager is None:
            raise RuntimeError("Token manager not attached")
        token = self._token_manager.get()
        parsed = self.request_raw(method, path, token=token, data=data, json=json, params=params)
        if is_token_expired(parsed) and self._config.enable_token_refresh:
            self._config.logger.debug("eskiz 401 on %s %s; refreshing token", method, path)
            token = self._token_manager.refresh_after_failure(token)
            parsed = self.request_raw(
                method, path, token=token, data=data, json=json, params=params
            )
            if is_token_expired(parsed):
                raise TokenInvalid(
                    "Token refresh produced a token that was rejected on retry",
                    status_code=parsed.status_code,
                )
        raise_for_response(parsed)
        return parsed

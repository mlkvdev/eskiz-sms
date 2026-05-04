"""Token managers — single-flight refresh for sync and async paths.

Both managers expose:

* ``get()`` — return the current bearer token, logging in on first use.
* ``refresh_after_failure(failed_token)`` — called by the transport when
  ``failed_token`` returned 401. Tries ``PATCH /auth/refresh`` first; on
  :class:`AuthError` it falls back to a fresh login.

Concurrent callers collapse onto a single in-flight auth call via a shared
:class:`Future` (sync) or :class:`asyncio.Future` (async). Locks are only
held for short critical sections — the HTTP round-trip itself happens
unguarded so queued callers don't wait under a held lock.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from concurrent.futures import Future
from typing import TYPE_CHECKING

from eskiz.exceptions import AuthError

if TYPE_CHECKING:
    from eskiz.auth.storage import TokenStorage


SyncLoginFn = Callable[[str, str], str]
SyncRefreshFn = Callable[[str], str]
AsyncLoginFn = Callable[[str, str], Awaitable[str]]
AsyncRefreshFn = Callable[[str], Awaitable[str]]


class SyncTokenManager:
    """Thread-safe token manager with single-flight refresh."""

    __slots__ = ("_email", "_in_flight", "_lock", "_login", "_password", "_refresh", "_storage")

    def __init__(
        self,
        email: str,
        password: str,
        storage: TokenStorage,
        login_fn: SyncLoginFn,
        refresh_fn: SyncRefreshFn,
    ) -> None:
        self._email = email
        self._password = password
        self._storage = storage
        self._login = login_fn
        self._refresh = refresh_fn
        self._lock = threading.Lock()
        self._in_flight: Future[str] | None = None

    def get(self) -> str:
        cached = self._storage.get()
        if cached:
            return cached
        return self._single_flight(self._do_login)

    def refresh_after_failure(self, failed_token: str) -> str:
        cached = self._storage.get()
        if cached and cached != failed_token:
            return cached
        return self._single_flight(lambda: self._do_refresh(failed_token))

    def invalidate(self) -> None:
        self._storage.clear()

    def _do_login(self) -> str:
        token = self._login(self._email, self._password)
        self._storage.set(token)
        return token

    def _do_refresh(self, failed_token: str) -> str:
        # Re-check inside the work — by the time we acquire the in-flight
        # slot, another thread may have stored a new token already.
        cached = self._storage.get()
        if cached and cached != failed_token:
            return cached
        try:
            token = self._refresh(failed_token)
        except AuthError:
            token = self._login(self._email, self._password)
        self._storage.set(token)
        return token

    def _single_flight(self, work: Callable[[], str]) -> str:
        with self._lock:
            if self._in_flight is None:
                future: Future[str] = Future()
                self._in_flight = future
                claim = True
            else:
                future = self._in_flight
                claim = False

        if not claim:
            # Wait outside the lock. ``future.result()`` re-raises any
            # exception the leader hit so all callers see the same outcome.
            return future.result()

        try:
            result = work()
            future.set_result(result)
            return result
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            with self._lock:
                self._in_flight = None


class AsyncTokenManager:
    """Task-safe token manager with single-flight refresh."""

    __slots__ = ("_email", "_in_flight", "_lock", "_login", "_password", "_refresh", "_storage")

    def __init__(
        self,
        email: str,
        password: str,
        storage: TokenStorage,
        login_fn: AsyncLoginFn,
        refresh_fn: AsyncRefreshFn,
    ) -> None:
        self._email = email
        self._password = password
        self._storage = storage
        self._login = login_fn
        self._refresh = refresh_fn
        # Lazy because the manager may be constructed outside an event loop.
        self._lock: asyncio.Lock | None = None
        self._in_flight: asyncio.Future[str] | None = None

    def _ensure_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get(self) -> str:
        cached = self._storage.get()
        if cached:
            return cached
        return await self._single_flight(self._do_login)

    async def refresh_after_failure(self, failed_token: str) -> str:
        cached = self._storage.get()
        if cached and cached != failed_token:
            return cached
        return await self._single_flight(lambda: self._do_refresh(failed_token))

    def invalidate(self) -> None:
        self._storage.clear()

    async def _do_login(self) -> str:
        token = await self._login(self._email, self._password)
        self._storage.set(token)
        return token

    async def _do_refresh(self, failed_token: str) -> str:
        cached = self._storage.get()
        if cached and cached != failed_token:
            return cached
        try:
            token = await self._refresh(failed_token)
        except AuthError:
            token = await self._login(self._email, self._password)
        self._storage.set(token)
        return token

    async def _single_flight(self, work: Callable[[], Awaitable[str]]) -> str:
        async with self._ensure_lock():
            if self._in_flight is None:
                future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
                self._in_flight = future
                claim = True
            else:
                future = self._in_flight
                claim = False

        if not claim:
            return await future

        try:
            result = await work()
            future.set_result(result)
            return result
        except BaseException as exc:
            future.set_exception(exc)
            raise
        finally:
            async with self._ensure_lock():
                self._in_flight = None

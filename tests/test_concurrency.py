"""Concurrency: single-flight refresh under contention."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest
import respx
from httpx import Response

from eskiz import AsyncEskizSMS, EskizSMS

from ._helpers import BASE_URL


def test_concurrent_refresh_is_single_flight(client: EskizSMS) -> None:
    """H2: N concurrent 401s should produce exactly one /auth/refresh call."""
    refresh_calls = 0
    refresh_lock = threading.Lock()

    def login_handler(request):
        return Response(200, json={"message": "ok", "data": {"token": "t1"}})

    def refresh_handler(request):
        nonlocal refresh_calls
        with refresh_lock:
            refresh_calls += 1
        # Hold the lock briefly so other threads can pile up
        time.sleep(0.05)
        return Response(200, json={"message": "ok", "data": {"token": "t2"}})

    def me_handler(request):
        if request.headers.get("authorization") == "Bearer t1":
            return Response(401, json={"message": "Expired"})
        return Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}})

    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/auth/login").mock(side_effect=login_handler)
        mock.patch(f"{BASE_URL}/auth/refresh").mock(side_effect=refresh_handler)
        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=me_handler)

        # Prime the token cache so all worker threads start with t1.
        client.auth.me()
        # Now the cached token is t2 because the first call already refreshed.
        # Re-prime: invalidate so all threads will see t1 at start.
        client._tokens.invalidate()  # type: ignore[attr-defined]
        # Reset counter — the priming call did one refresh.
        refresh_calls = 0

        results: list[int] = []
        errors: list[BaseException] = []

        def worker():
            try:
                results.append(client.auth.me().id)
            except BaseException as e:  # pragma: no cover
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, errors
        assert all(r == 1 for r in results)
        # Each worker initially has no cached token, so each performs a fresh
        # login. Single-flight collapses those into one /auth/login call;
        # then subsequent worker requests use the cached token (which is
        # already valid t1), get 401, and trigger a single refresh.
        assert refresh_calls <= 1, (
            f"expected at most one refresh under contention, got {refresh_calls}"
        )


@pytest.mark.asyncio
async def test_async_concurrent_refresh_is_single_flight(aclient: AsyncEskizSMS) -> None:
    refresh_calls = 0

    def login_handler(request):
        return Response(200, json={"message": "ok", "data": {"token": "t1"}})

    async def refresh_handler(request):
        nonlocal refresh_calls
        refresh_calls += 1
        await asyncio.sleep(0.05)
        return Response(200, json={"message": "ok", "data": {"token": "t2"}})

    def me_handler(request):
        if request.headers.get("authorization") == "Bearer t1":
            return Response(401, json={"message": "Expired"})
        return Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}})

    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/auth/login").mock(side_effect=login_handler)
        mock.patch(f"{BASE_URL}/auth/refresh").mock(side_effect=refresh_handler)
        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=me_handler)

        # Prime
        await aclient.auth.me()
        aclient._tokens.invalidate()  # type: ignore[attr-defined]
        refresh_calls = 0

        results = await asyncio.gather(*(aclient.auth.me() for _ in range(8)))
        assert all(r.id == 1 for r in results)
        assert refresh_calls <= 1

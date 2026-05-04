"""Shared test helpers — building respx mocks for the standard auth flow."""

from __future__ import annotations

import respx
from httpx import Response

BASE_URL = "https://notify.eskiz.uz/api"


def mock_login(mock: respx.MockRouter, *, token: str = "tok-1") -> respx.Route:
    return mock.post(f"{BASE_URL}/auth/login").mock(
        return_value=Response(200, json={"message": "token_generated", "data": {"token": token}})
    )


def mock_refresh(mock: respx.MockRouter, *, token: str = "tok-2") -> respx.Route:
    return mock.patch(f"{BASE_URL}/auth/refresh").mock(
        return_value=Response(200, json={"message": "token_generated", "data": {"token": token}})
    )

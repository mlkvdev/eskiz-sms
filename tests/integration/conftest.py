"""Fixtures for the live-API integration suite.

These tests hit the real Eskiz endpoint at ``ESKIZ_BASE_URL`` (defaulting to
``https://notify.eskiz.uz/api``). They are opt-in: the root ``conftest`` skips
anything marked ``integration`` unless ``--run-integration`` is passed.

Credentials are loaded from environment variables. A local ``.env.integration``
file is loaded automatically if present; see ``.env.integration.example``.

Required:
    ESKIZ_EMAIL, ESKIZ_PASSWORD

Optional:
    ESKIZ_BASE_URL    Override API base URL.
    ESKIZ_TEST_PHONE  E.164 number that should receive a real test SMS. Tests
                      that actually send SMS are skipped unless this is set —
                      this keeps an unsuspecting integration run from burning
                      credits.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest

from eskiz import AsyncEskizSMS, EskizSMS

ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env.integration"


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ENV_FILE, override=False)


_load_env_file()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} not set; skipping integration test")
    return value


@pytest.fixture(scope="session")
def integration_kwargs() -> dict[str, Any]:
    return {
        "email": _require("ESKIZ_EMAIL"),
        "password": _require("ESKIZ_PASSWORD"),
        "base_url": os.environ.get("ESKIZ_BASE_URL", "https://notify.eskiz.uz/api"),
        "timeout": 20.0,
    }


@pytest.fixture
def live_client(integration_kwargs: dict[str, Any]) -> Iterator[EskizSMS]:
    with EskizSMS(**integration_kwargs) as c:
        yield c


@pytest.fixture
async def live_aclient(integration_kwargs: dict[str, Any]) -> AsyncIterator[AsyncEskizSMS]:
    async with AsyncEskizSMS(**integration_kwargs) as c:
        yield c


@pytest.fixture(scope="session")
def test_phone() -> str:
    phone = os.environ.get("ESKIZ_TEST_PHONE")
    if not phone:
        pytest.skip("ESKIZ_TEST_PHONE not set; skipping send test")
    return phone

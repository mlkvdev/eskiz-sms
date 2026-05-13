"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from eskiz import AsyncEskizSMS, EskizSMS

from ._helpers import BASE_URL


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked `integration` against the real Eskiz API.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(reason="needs --run-integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture
def client():
    with EskizSMS(email="user@example.com", password="hunter2", base_url=BASE_URL) as c:
        yield c


@pytest.fixture
async def aclient():
    async with AsyncEskizSMS(email="user@example.com", password="hunter2", base_url=BASE_URL) as c:
        yield c

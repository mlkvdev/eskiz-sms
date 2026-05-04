"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from eskiz import AsyncEskizSMS, Config, EskizSMS

BASE_URL = "https://notify.eskiz.uz/api"


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
def config() -> Config:
    return Config(email="user@example.com", password="hunter2", base_url=BASE_URL)


@pytest.fixture
def client(config: Config):
    with EskizSMS(config) as c:
        yield c


@pytest.fixture
async def aclient(config: Config):
    async with AsyncEskizSMS(config) as c:
        yield c

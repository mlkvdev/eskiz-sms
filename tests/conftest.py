"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from eskiz import AsyncEskizSMS, Config, EskizSMS

BASE_URL = "https://notify.eskiz.uz/api"


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

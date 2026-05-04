"""Token-storage backends."""

from __future__ import annotations

from pathlib import Path

import respx
from httpx import Response

from eskiz import Config, DotenvTokenStorage, EskizSMS, MemoryTokenStorage

from ._helpers import BASE_URL, mock_login


def test_memory_storage_roundtrip() -> None:
    s = MemoryTokenStorage()
    assert s.get() is None
    s.set("abc")
    assert s.get() == "abc"
    s.clear()
    assert s.get() is None


def test_memory_storage_initial_value() -> None:
    s = MemoryTokenStorage(initial="seed")
    assert s.get() == "seed"


def test_dotenv_storage_roundtrip(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    s = DotenvTokenStorage(env_path=env)

    assert s.get() is None  # file doesn't exist yet

    s.set("tok-xyz")
    assert env.read_text().strip().startswith("ESKIZ_TOKEN=")
    assert s.get() == "tok-xyz"

    s.set("tok-2")
    assert s.get() == "tok-2"

    s.clear()
    assert s.get() is None


def test_dotenv_storage_custom_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    s = DotenvTokenStorage(env_path=env, key="MY_TOKEN")
    s.set("hello")
    assert "MY_TOKEN=" in env.read_text()
    assert s.get() == "hello"


def test_dotenv_storage_clear_no_file(tmp_path: Path) -> None:
    """clear() must not raise when the .env file doesn't exist."""
    env = tmp_path / "nonexistent.env"
    s = DotenvTokenStorage(env_path=env)
    s.clear()  # no-op, no exception


def test_client_uses_dotenv_storage(tmp_path: Path) -> None:
    """Client persists token to dotenv file on first login."""
    env = tmp_path / ".env"
    storage = DotenvTokenStorage(env_path=env)
    cfg = Config(
        email="u@e.com",
        password="p",
        base_url=BASE_URL,
        token_storage=storage,
    )

    with respx.mock() as mock, EskizSMS(cfg) as client:
        login = mock_login(mock, token="tok-from-login")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}}
            )
        )

        client.auth.me()
        assert login.call_count == 1
        # Token persisted
        assert "ESKIZ_TOKEN=tok-from-login" in env.read_text() or storage.get() == "tok-from-login"

    # A second client with the same storage should reuse the cached token
    storage2 = DotenvTokenStorage(env_path=env)
    cfg2 = Config(
        email="u@e.com",
        password="p",
        base_url=BASE_URL,
        token_storage=storage2,
    )
    with respx.mock(assert_all_called=False) as mock, EskizSMS(cfg2) as client2:
        login2 = mock_login(mock, token="tok-not-used")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}}
            )
        )

        client2.auth.me()
        assert login2.call_count == 0, "should reuse token from dotenv file"

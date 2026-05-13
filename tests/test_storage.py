"""Token-storage backends."""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import pytest
import respx
from httpx import Response

from eskiz import DotenvTokenStorage, EskizSMS, MemoryTokenStorage

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


@pytest.mark.skipif(
    sys.platform == "win32", reason="POSIX file modes are meaningless on Windows"
)
def test_dotenv_storage_chmods_only_on_creation(tmp_path: Path) -> None:
    """Newly created token files are locked to 0o600; existing files keep their perms.

    The latter matters when the caller points this backend at an existing
    .env holding other env vars — we mustn't trample on perms the user
    set deliberately (e.g. 0o644 so a non-root systemd unit can read it).
    """
    new_env = tmp_path / "new.env"
    s = DotenvTokenStorage(env_path=new_env)
    s.set("sekret")
    assert stat.S_IMODE(new_env.stat().st_mode) == 0o600

    # An existing file with looser perms must be left alone.
    shared = tmp_path / "shared.env"
    shared.write_text("OTHER=value\n")
    shared.chmod(0o644)
    s2 = DotenvTokenStorage(env_path=shared)
    s2.set("tok")
    assert stat.S_IMODE(shared.stat().st_mode) == 0o644, (
        "must not tighten perms on a pre-existing file"
    )
    contents = shared.read_text()
    assert "OTHER=value" in contents
    assert "ESKIZ_TOKEN=" in contents and "tok" in contents
    assert s2.get() == "tok"


def test_dotenv_storage_clear_no_file(tmp_path: Path) -> None:
    """clear() must not raise when the .env file doesn't exist."""
    env = tmp_path / "nonexistent.env"
    s = DotenvTokenStorage(env_path=env)
    s.clear()  # no-op, no exception


def test_client_uses_dotenv_storage(tmp_path: Path) -> None:
    """Client persists token to dotenv file on first login."""
    env = tmp_path / ".env"
    storage = DotenvTokenStorage(env_path=env)
    with (
        respx.mock() as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            token_storage=storage,
        ) as client,
    ):
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
    with (
        respx.mock(assert_all_called=False) as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            token_storage=storage2,
        ) as client2,
    ):
        login2 = mock_login(mock, token="tok-not-used")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}}
            )
        )

        client2.auth.me()
        assert login2.call_count == 0, "should reuse token from dotenv file"

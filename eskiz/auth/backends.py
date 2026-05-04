"""Optional token-storage backends.

Each backend imports its third-party dependency lazily so the core SDK stays
free of optional installs. Use :class:`DotenvTokenStorage` only after
installing the ``dotenv`` extra::

    pip install "eskiz-sms[dotenv]"
"""

from __future__ import annotations

import threading
from pathlib import Path

DEFAULT_ENV_PATH = ".env"
DEFAULT_KEY = "ESKIZ_TOKEN"


class DotenvTokenStorage:
    """Token storage backed by a ``.env`` file via ``python-dotenv``.

    Reads and writes a single key (default ``ESKIZ_TOKEN``) in the file at
    ``env_path``. The file is created on first :meth:`set` if missing.
    Operations are serialized with a per-instance lock — sufficient for
    single-process use; cross-process callers should add their own locking.
    """

    __slots__ = ("_env_path", "_key", "_lock")

    def __init__(
        self,
        env_path: str | Path = DEFAULT_ENV_PATH,
        key: str = DEFAULT_KEY,
    ) -> None:
        try:
            import dotenv  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "DotenvTokenStorage requires python-dotenv. "
                "Install with: pip install 'eskiz-sms[dotenv]'"
            ) from exc
        self._env_path = str(env_path)
        self._key = key
        self._lock = threading.Lock()

    def get(self) -> str | None:
        from dotenv import get_key

        with self._lock:
            if not Path(self._env_path).exists():
                return None
            value = get_key(dotenv_path=self._env_path, key_to_get=self._key)
            return value or None

    def set(self, token: str) -> None:
        from dotenv import set_key

        with self._lock:
            Path(self._env_path).touch(exist_ok=True)
            set_key(self._env_path, key_to_set=self._key, value_to_set=token)

    def clear(self) -> None:
        from dotenv import unset_key

        with self._lock:
            if not Path(self._env_path).exists():
                return
            unset_key(self._env_path, key_to_unset=self._key)

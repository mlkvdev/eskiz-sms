"""Optional token-storage backends.

Each backend imports its third-party dependency lazily so the core SDK stays
free of optional installs. Use :class:`DotenvTokenStorage` only after
installing the ``dotenv`` extra::

    pip install "eskiz-sms[dotenv]"

``DotenvTokenStorage`` performs blocking file I/O under a per-instance lock.
That is fine for the sync client; under ``AsyncEskizSMS`` each ``get``/``set``
briefly blocks the event loop while the file is read or rewritten. For a
token that effectively never changes between processes this is acceptable;
high-fanout deployments should plug in a Redis- or DB-backed storage.
"""

from __future__ import annotations

import contextlib
import threading
from importlib.util import find_spec
from pathlib import Path

DEFAULT_ENV_PATH = ".env"
DEFAULT_KEY = "ESKIZ_TOKEN"


class DotenvTokenStorage:
    """Token storage backed by a ``.env`` file via ``python-dotenv``.

    Reads and writes a single key (default ``ESKIZ_TOKEN``) in the file at
    ``env_path``.

    **File permissions.** When the file does not exist yet, this backend
    creates it with ``0o600`` (best-effort — skipped on platforms where
    POSIX modes are meaningless, e.g. Windows) so the bearer token isn't
    world-readable under a default umask. If the file *already* exists
    its permissions are left alone — point this backend at an existing
    ``.env`` that holds other vars and the rest of the file (and any
    sharing arrangements you have) won't be disturbed.

    If you keep the token next to other secrets and want them all locked
    down, set the perms yourself once with ``chmod 600 .env`` and the
    SDK's writes will preserve them.

    Operations are serialized with a per-instance lock — sufficient for
    single-process use; cross-process callers should add their own locking.
    """

    __slots__ = ("_env_path", "_key", "_lock")

    def __init__(
        self,
        env_path: str | Path = DEFAULT_ENV_PATH,
        key: str = DEFAULT_KEY,
    ) -> None:
        if find_spec("dotenv") is None:
            raise ImportError(
                "DotenvTokenStorage requires python-dotenv. "
                "Install with: pip install 'eskiz-sms[dotenv]'"
            )
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
            path = Path(self._env_path)
            # Only lock down perms on files we created — leave pre-existing
            # files alone so the SDK doesn't trample on a shared .env that
            # may have been deliberately set looser.
            was_new = not path.exists()
            path.touch(exist_ok=True)
            if was_new:
                with contextlib.suppress(OSError):
                    path.chmod(0o600)
            set_key(self._env_path, key_to_set=self._key, value_to_set=token)

    def clear(self) -> None:
        from dotenv import unset_key

        with self._lock:
            if not Path(self._env_path).exists():
                return
            unset_key(self._env_path, key_to_unset=self._key)

"""Auth resource — currently exposes only ``me()``.

Login and refresh wire formats live in :mod:`eskiz._protocol.auth` and are
called by the token manager via the executor; they are not part of the
public surface.
"""

from __future__ import annotations

from eskiz._protocol import auth as _proto
from eskiz.models import User
from eskiz.resources._base import _AsyncResource, _SyncResource


class AuthResource(_SyncResource):
    def me(self) -> User:
        return self._exec.run(_proto.me())


class AsyncAuthResource(_AsyncResource):
    async def me(self) -> User:
        return await self._exec.run(_proto.me())

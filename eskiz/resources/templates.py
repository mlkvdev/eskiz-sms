"""Templates resource."""

from __future__ import annotations

from eskiz._protocol import templates as _proto
from eskiz.models import TemplateCreated, TemplateList
from eskiz.resources._base import _AsyncResource, _SyncResource


class TemplatesResource(_SyncResource):
    def create(self, template: str) -> TemplateCreated:
        return self._exec.run(_proto.create(template))

    def list_all(self) -> TemplateList:
        return self._exec.run(_proto.list_())


class AsyncTemplatesResource(_AsyncResource):
    async def create(self, template: str) -> TemplateCreated:
        return await self._exec.run(_proto.create(template))

    async def list_all(self) -> TemplateList:
        return await self._exec.run(_proto.list_())

"""SMS resource — send, query, status, utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eskiz._protocol import sms as _proto
from eskiz.models import (
    BatchMessage,
    BatchSendResult,
    DispatchStatusRow,
    NormalizerCharacter,
    PaginatedMessages,
    SendResult,
    SmsCheckResult,
    SmsStatusDetail,
)
from eskiz.resources._base import AsyncResource, SyncResource


class SmsResource(SyncResource):
    def send(
        self,
        *,
        mobile_phone: str,
        message: str,
        from_whom: str | None = None,
        callback_url: str | None = None,
    ) -> SendResult:
        return self._exec.run(
            _proto.send(
                mobile_phone=mobile_phone,
                message=message,
                from_whom=from_whom or self._config.from_whom,
                callback_url=callback_url or self._config.callback_url,
            )
        )

    def send_global(
        self,
        *,
        mobile_phone: str,
        message: str,
        country_code: str,
        callback_url: str | None = None,
        unicode: bool = False,
    ) -> SendResult:
        return self._exec.run(
            _proto.send_global(
                mobile_phone=mobile_phone,
                message=message,
                country_code=country_code,
                callback_url=callback_url or self._config.callback_url,
                unicode=unicode,
            )
        )

    def send_batch(
        self,
        *,
        messages: list[BatchMessage] | list[dict[str, Any]],
        dispatch_id: int,
        from_whom: str | None = None,
        callback_url: str | None = None,
    ) -> BatchSendResult:
        return self._exec.run(
            _proto.send_batch(
                messages=messages,
                dispatch_id=dispatch_id,
                from_whom=from_whom or self._config.from_whom,
                callback_url=callback_url or self._config.callback_url,
            )
        )

    def list_messages(
        self,
        *,
        start_date: datetime | str,
        to_date: datetime | str,
        page_size: int = 20,
        count: int = 0,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> PaginatedMessages:
        return self._exec.run(
            _proto.list_messages(
                start_date=start_date,
                to_date=to_date,
                page_size=page_size,
                count=count,
                is_ad=is_ad,
                status=status,
            )
        )

    def list_by_dispatch(
        self,
        *,
        dispatch_id: int,
        count: int = 0,
        is_ad: bool | None = None,
        status: str | None = None,
        page_size: int | None = None,
    ) -> PaginatedMessages:
        return self._exec.run(
            _proto.list_by_dispatch(
                dispatch_id=dispatch_id,
                count=count,
                is_ad=is_ad,
                status=status,
                page_size=page_size,
            )
        )

    def dispatch_status(self, *, dispatch_id: int, user_id: int) -> list[DispatchStatusRow]:
        return self._exec.run(_proto.dispatch_status(dispatch_id=dispatch_id, user_id=user_id))

    def status(self, sms_id: str | int) -> SmsStatusDetail:
        return self._exec.run(_proto.status(sms_id))

    def nicks(self) -> list[str]:
        return self._exec.run(_proto.nicks())

    def normalize(self, message: str) -> list[NormalizerCharacter]:
        return self._exec.run(_proto.normalize(message))

    def check(self, message: str) -> SmsCheckResult:
        return self._exec.run(_proto.check(message))


class AsyncSmsResource(AsyncResource):
    async def send(
        self,
        *,
        mobile_phone: str,
        message: str,
        from_whom: str | None = None,
        callback_url: str | None = None,
    ) -> SendResult:
        return await self._exec.run(
            _proto.send(
                mobile_phone=mobile_phone,
                message=message,
                from_whom=from_whom or self._config.from_whom,
                callback_url=callback_url or self._config.callback_url,
            )
        )

    async def send_global(
        self,
        *,
        mobile_phone: str,
        message: str,
        country_code: str,
        callback_url: str | None = None,
        unicode: bool = False,
    ) -> SendResult:
        return await self._exec.run(
            _proto.send_global(
                mobile_phone=mobile_phone,
                message=message,
                country_code=country_code,
                callback_url=callback_url or self._config.callback_url,
                unicode=unicode,
            )
        )

    async def send_batch(
        self,
        *,
        messages: list[BatchMessage] | list[dict[str, Any]],
        dispatch_id: int,
        from_whom: str | None = None,
        callback_url: str | None = None,
    ) -> BatchSendResult:
        return await self._exec.run(
            _proto.send_batch(
                messages=messages,
                dispatch_id=dispatch_id,
                from_whom=from_whom or self._config.from_whom,
                callback_url=callback_url or self._config.callback_url,
            )
        )

    async def list_messages(
        self,
        *,
        start_date: datetime | str,
        to_date: datetime | str,
        page_size: int = 20,
        count: int = 0,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> PaginatedMessages:
        return await self._exec.run(
            _proto.list_messages(
                start_date=start_date,
                to_date=to_date,
                page_size=page_size,
                count=count,
                is_ad=is_ad,
                status=status,
            )
        )

    async def list_by_dispatch(
        self,
        *,
        dispatch_id: int,
        count: int = 0,
        is_ad: bool | None = None,
        status: str | None = None,
        page_size: int | None = None,
    ) -> PaginatedMessages:
        return await self._exec.run(
            _proto.list_by_dispatch(
                dispatch_id=dispatch_id,
                count=count,
                is_ad=is_ad,
                status=status,
                page_size=page_size,
            )
        )

    async def dispatch_status(self, *, dispatch_id: int, user_id: int) -> list[DispatchStatusRow]:
        return await self._exec.run(
            _proto.dispatch_status(dispatch_id=dispatch_id, user_id=user_id)
        )

    async def status(self, sms_id: str | int) -> SmsStatusDetail:
        return await self._exec.run(_proto.status(sms_id))

    async def nicks(self) -> list[str]:
        return await self._exec.run(_proto.nicks())

    async def normalize(self, message: str) -> list[NormalizerCharacter]:
        return await self._exec.run(_proto.normalize(message))

    async def check(self, message: str) -> SmsCheckResult:
        return await self._exec.run(_proto.check(message))

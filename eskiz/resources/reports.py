"""Reports resource — totals, balance, prices, exports, logs."""

from __future__ import annotations

from datetime import datetime

from eskiz._protocol import reports as _proto
from eskiz.models import (
    DispatchExpense,
    LimitInfo,
    PriceList,
    RangeExpense,
    SmscTotal,
    SmsLogResponse,
    Total,
    TotalByMonth,
)
from eskiz.resources._base import _AsyncResource, _SyncResource


class ReportsResource(_SyncResource):
    def balance(self) -> LimitInfo:
        return self._exec.run(_proto.balance())

    def prices(self) -> PriceList:
        return self._exec.run(_proto.prices())

    def totals(self, *, year: int, month: int, is_global: bool = False) -> list[Total]:
        return self._exec.run(_proto.totals(year=year, month=month, is_global=is_global))

    def by_month(self, year: int) -> list[TotalByMonth]:
        return self._exec.run(_proto.by_month(year))

    def by_smsc(self, *, year: int, month: int) -> list[SmscTotal]:
        return self._exec.run(_proto.by_smsc(year=year, month=month))

    def by_range(
        self,
        *,
        start_date: datetime | str,
        to_date: datetime | str,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> list[RangeExpense]:
        return self._exec.run(
            _proto.by_range(start_date=start_date, to_date=to_date, is_ad=is_ad, status=status)
        )

    def by_dispatch(
        self,
        *,
        dispatch_id: int,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> list[DispatchExpense]:
        return self._exec.run(
            _proto.by_dispatch(dispatch_id=dispatch_id, is_ad=is_ad, status=status)
        )

    def export(
        self,
        *,
        year: int,
        month: int,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        status: str = "all",
    ) -> str:
        return self._exec.run(
            _proto.export(year=year, month=month, start=start, end=end, status=status)
        )

    def logs(self, sms_id: str | int) -> SmsLogResponse:
        return self._exec.run(_proto.logs(sms_id))


class AsyncReportsResource(_AsyncResource):
    async def balance(self) -> LimitInfo:
        return await self._exec.run(_proto.balance())

    async def prices(self) -> PriceList:
        return await self._exec.run(_proto.prices())

    async def totals(self, *, year: int, month: int, is_global: bool = False) -> list[Total]:
        return await self._exec.run(_proto.totals(year=year, month=month, is_global=is_global))

    async def by_month(self, year: int) -> list[TotalByMonth]:
        return await self._exec.run(_proto.by_month(year))

    async def by_smsc(self, *, year: int, month: int) -> list[SmscTotal]:
        return await self._exec.run(_proto.by_smsc(year=year, month=month))

    async def by_range(
        self,
        *,
        start_date: datetime | str,
        to_date: datetime | str,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> list[RangeExpense]:
        return await self._exec.run(
            _proto.by_range(start_date=start_date, to_date=to_date, is_ad=is_ad, status=status)
        )

    async def by_dispatch(
        self,
        *,
        dispatch_id: int,
        is_ad: bool | None = None,
        status: str | None = None,
    ) -> list[DispatchExpense]:
        return await self._exec.run(
            _proto.by_dispatch(dispatch_id=dispatch_id, is_ad=is_ad, status=status)
        )

    async def export(
        self,
        *,
        year: int,
        month: int,
        start: datetime | str | None = None,
        end: datetime | str | None = None,
        status: str = "all",
    ) -> str:
        return await self._exec.run(
            _proto.export(year=year, month=month, start=start, end=end, status=status)
        )

    async def logs(self, sms_id: str | int) -> SmsLogResponse:
        return await self._exec.run(_proto.logs(sms_id))

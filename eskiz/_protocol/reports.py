"""Reports protocol — totals, balance, prices, exports, logs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eskiz import endpoints as ep
from eskiz._protocol import RequestPlan
from eskiz._protocol._helpers import (
    bool_flag,
    datetime_str,
    envelope_data,
    envelope_list_parser,
    unexpected_shape,
)
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
from eskiz.transport.base import RawResponse


def balance() -> RequestPlan[LimitInfo]:
    return RequestPlan(
        method="GET",
        path=ep.USER_LIMIT,
        parse=lambda r: LimitInfo.model_validate(envelope_data(r.data)),
    )


def prices() -> RequestPlan[PriceList]:
    def parse(r: RawResponse) -> PriceList:
        if not isinstance(r.data, dict):
            raise unexpected_shape(r.data, status_code=r.status_code)
        return PriceList.model_validate(r.data)

    return RequestPlan(method="GET", path=ep.USER_PRICES, parse=parse)


def totals(*, year: int, month: int, is_global: bool = False) -> RequestPlan[list[Total]]:
    return RequestPlan(
        method="POST",
        path=ep.USER_TOTALS,
        data={"year": year, "month": month, "is_global": "1" if is_global else "0"},
        parse=envelope_list_parser(Total.model_validate),
    )


def by_month(year: int) -> RequestPlan[list[TotalByMonth]]:
    return RequestPlan(
        method="GET",
        path=ep.REPORT_TOTAL_BY_MONTH,
        params={"year": year},
        parse=envelope_list_parser(TotalByMonth.model_validate),
    )


def by_smsc(*, year: int, month: int) -> RequestPlan[list[SmscTotal]]:
    return RequestPlan(
        method="POST",
        path=ep.REPORT_TOTAL_BY_SMSC,
        data={"year": year, "month": month},
        parse=envelope_list_parser(SmscTotal.model_validate),
    )


def by_range(
    *,
    start_date: datetime | str,
    to_date: datetime | str,
    is_ad: bool | None = None,
    status: str | None = None,
) -> RequestPlan[list[RangeExpense]]:
    body: dict[str, Any] = {
        "start_date": datetime_str(start_date),
        "to_date": datetime_str(to_date),
    }
    flag = bool_flag(is_ad)
    if flag is not None:
        body["is_ad"] = flag
    params = {"status": status} if status is not None else None
    return RequestPlan(
        method="POST",
        path=ep.REPORT_TOTAL_BY_RANGE,
        data=body,
        params=params,
        parse=envelope_list_parser(RangeExpense.model_validate),
    )


def by_dispatch(
    *,
    dispatch_id: int,
    is_ad: bool | None = None,
    status: str | None = None,
) -> RequestPlan[list[DispatchExpense]]:
    body: dict[str, Any] = {"dispatch_id": dispatch_id}
    flag = bool_flag(is_ad)
    if flag is not None:
        body["is_ad"] = flag
    params = {"status": status} if status is not None else None
    return RequestPlan(
        method="POST",
        path=ep.REPORT_TOTAL_BY_DISPATCH,
        data=body,
        params=params,
        parse=envelope_list_parser(DispatchExpense.model_validate),
    )


def export(
    *,
    year: int,
    month: int,
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    status: str = "all",
) -> RequestPlan[str]:
    body: dict[str, Any] = {"year": year, "month": month}
    if start is not None:
        body["start"] = datetime_str(start)
    if end is not None:
        body["end"] = datetime_str(end)
    def parse_export(r: RawResponse) -> str:
        if not isinstance(r.data, str):
            raise unexpected_shape(r.data, status_code=r.status_code)
        return r.data

    return RequestPlan(
        method="POST",
        path=ep.MESSAGE_EXPORT,
        data=body,
        params={"status": status},
        parse=parse_export,
    )


def logs(sms_id: str | int) -> RequestPlan[SmsLogResponse]:
    def parse(r: RawResponse) -> SmsLogResponse:
        if not isinstance(r.data, dict):
            raise unexpected_shape(r.data, status_code=r.status_code)
        return SmsLogResponse.model_validate(r.data)

    return RequestPlan(method="GET", path=ep.sms_log(sms_id), parse=parse)

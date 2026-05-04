"""SMS protocol — send, query, status, utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from eskiz import endpoints as ep
from eskiz._protocol import RequestPlan
from eskiz._protocol._helpers import (
    apply_callback,
    bool_flag,
    datetime_str,
    envelope_data,
    envelope_list_parser,
    normalize_batch_messages,
)
from eskiz._validators import normalize_phone
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
from eskiz.transport.base import RawResponse


def send(
    *,
    mobile_phone: str,
    message: str,
    from_whom: str,
    callback_url: str | None = None,
) -> RequestPlan[SendResult]:
    body: dict[str, Any] = {
        "mobile_phone": normalize_phone(mobile_phone),
        "message": message,
        "from": from_whom,
    }
    apply_callback(body, callback_url)
    return RequestPlan(
        method="POST",
        path=ep.SEND_SMS,
        data=body,
        parse=lambda r: SendResult.model_validate(r.data),
    )


def send_global(
    *,
    mobile_phone: str,
    message: str,
    country_code: str,
    callback_url: str | None = None,
    unicode: bool = False,
) -> RequestPlan[SendResult]:
    body: dict[str, Any] = {
        "mobile_phone": normalize_phone(mobile_phone),
        "message": message,
        "country_code": country_code,
        "unicode": "1" if unicode else "0",
    }
    apply_callback(body, callback_url)
    return RequestPlan(
        method="POST",
        path=ep.SEND_GLOBAL_SMS,
        data=body,
        parse=lambda r: SendResult.model_validate(r.data),
    )


def send_batch(
    *,
    messages: list[BatchMessage] | list[dict[str, Any]],
    dispatch_id: int,
    from_whom: str,
    callback_url: str | None = None,
) -> RequestPlan[BatchSendResult]:
    body: dict[str, Any] = {
        "messages": normalize_batch_messages(messages),
        "from": from_whom,
        "dispatch_id": dispatch_id,
    }
    apply_callback(body, callback_url)
    return RequestPlan(
        method="POST",
        path=ep.SEND_BATCH_SMS,
        json=body,
        parse=lambda r: BatchSendResult.model_validate(r.data),
    )


def list_messages(
    *,
    start_date: datetime | str,
    to_date: datetime | str,
    page_size: int = 20,
    count: int = 0,
    is_ad: bool | None = None,
    status: str | None = None,
) -> RequestPlan[PaginatedMessages]:
    body: dict[str, Any] = {
        "start_date": datetime_str(start_date),
        "to_date": datetime_str(to_date),
        "page_size": page_size,
        "count": count,
    }
    flag = bool_flag(is_ad)
    if flag is not None:
        body["is_ad"] = flag
    params = {"status": status} if status is not None else None
    return RequestPlan(
        method="POST",
        path=ep.USER_MESSAGES,
        data=body,
        params=params,
        parse=lambda r: PaginatedMessages.model_validate(envelope_data(r.data)),
    )


def list_by_dispatch(
    *,
    dispatch_id: int,
    count: int = 0,
    is_ad: bool | None = None,
    status: str | None = None,
    page_size: int | None = None,
) -> RequestPlan[PaginatedMessages]:
    body: dict[str, Any] = {"dispatch_id": dispatch_id, "count": count}
    flag = bool_flag(is_ad)
    if flag is not None:
        body["is_ad"] = flag
    params: dict[str, Any] = {}
    if status is not None:
        params["status"] = status
    if page_size is not None:
        params["page-size"] = page_size

    def parse(r: RawResponse) -> PaginatedMessages:
        payload = r.data
        if isinstance(payload, dict) and "data" in payload:
            payload = payload["data"]
        if isinstance(payload, dict):
            return PaginatedMessages.model_validate(payload)
        return PaginatedMessages(result=[])

    return RequestPlan(
        method="POST",
        path=ep.USER_MESSAGES_BY_DISPATCH,
        data=body,
        params=params or None,
        parse=parse,
    )


def dispatch_status(*, dispatch_id: int, user_id: int) -> RequestPlan[list[DispatchStatusRow]]:
    return RequestPlan(
        method="POST",
        path=ep.DISPATCH_STATUS,
        data={"user_id": user_id, "dispatch_id": dispatch_id},
        parse=envelope_list_parser(DispatchStatusRow.model_validate),
    )


def status(sms_id: str | int) -> RequestPlan[SmsStatusDetail]:
    return RequestPlan(
        method="GET",
        path=ep.sms_status_by_id(sms_id),
        parse=lambda r: SmsStatusDetail.model_validate(envelope_data(r.data)),
    )


def nicks() -> RequestPlan[list[str]]:
    def parse(r: RawResponse) -> list[str]:
        return [str(x) for x in r.data] if isinstance(r.data, list) else []

    return RequestPlan(method="GET", path=ep.NICK_ME, parse=parse)


def normalize(message: str) -> RequestPlan[list[NormalizerCharacter]]:
    def parse(r: RawResponse) -> list[NormalizerCharacter]:
        if isinstance(r.data, dict):
            chars = r.data.get("special_characters", [])
            return [NormalizerCharacter.model_validate(c) for c in chars]
        return []

    return RequestPlan(
        method="POST",
        path=ep.SMS_NORMALIZER,
        data={"message": message},
        parse=parse,
    )


def check(message: str) -> RequestPlan[SmsCheckResult]:
    return RequestPlan(
        method="POST",
        path=ep.SMS_CHECK,
        json={"message": message},
        parse=lambda r: SmsCheckResult.model_validate(envelope_data(r.data)),
    )

"""SMS-related models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from eskiz._validators import normalize_phone
from eskiz.models.common import BaseEskizModel


class SendResult(BaseEskizModel):
    """Result of single-recipient or international send.

    Eskiz returns the body bare (no envelope) with ``id``, ``message``, ``status``.
    For batch, ``status`` is a list — see :class:`BatchSendResult`.
    """

    id: str | int | None = None
    message: str | None = None
    status: str | None = None


class BatchMessage(BaseEskizModel):
    """One entry in a batch send request."""

    user_sms_id: str = Field(..., description="Caller-supplied unique id for tracking.")
    to: str = Field(..., description="Recipient phone, digits only.")
    text: str = Field(..., description="Message body.")

    @field_validator("to", mode="before")
    @classmethod
    def _coerce_to(cls, value: object) -> str:
        return normalize_phone(str(value))


class BatchSendResult(BaseEskizModel):
    """Result of a batch send."""

    id: str | int | None = None
    message: str | None = None
    status: list[str] | None = None


class DispatchStatusRow(BaseEskizModel):
    """One bucket in the dispatch-status aggregation."""

    status: str
    total: int


class PaginatedMessages(BaseEskizModel):
    """Paginated list returned by ``/message/sms/get-user-messages``."""

    current_page: int | None = None
    per_page: int | None = None
    last_page: int | None = None
    total: int | None = None
    from_: int | None = Field(default=None, alias="from")
    to: int | None = None
    path: str | None = None
    next_page_url: str | None = None
    prev_page_url: str | None = None
    first_page_url: str | None = None
    last_page_url: str | None = None
    data: list[dict[str, Any]] | None = None
    # ``result`` may be a list of message rows or a free-form status string
    # (e.g. when a by-dispatch query has no detailized data).
    result: list[dict[str, Any]] | str | None = None


class NormalizerCharacter(BaseEskizModel):
    """One special character flagged by ``/message/sms/normalizer``."""

    position: int
    code: str
    char: str


class SmsCheckInfo(BaseEskizModel):
    """One SMSC entry in the SMS check response."""

    smsc: int
    is_ad: bool
    price: int | float
    is_error: bool
    error: str = ""


class SmsCheckResult(BaseEskizModel):
    """``/message/sms/check`` response payload."""

    user_id: int | None = None
    info: list[SmsCheckInfo]


class SmsLogEntry(BaseEskizModel):
    """One entry in ``/logs/sms/{id}`` system logs."""

    ip: str | None = None
    from_: str | None = Field(default=None, alias="from")
    to: str | None = None
    dispatch_id: str | int | None = None
    user_sms_id: str | None = None
    timestamp: datetime | None = None
    message: str | None = None
    full_message: str | None = None
    level_name: str | None = None


class SmsLogResponse(BaseEskizModel):
    """Wrapper for system logs."""

    messages: list[SmsLogEntry]


class SmsStatusDetail(BaseEskizModel):
    """Detailed per-message status from ``/message/sms/status_by_id/{id}``.

    The Eskiz response is rich; we keep typed fields for the common ones.
    Unknown fields are silently dropped (the SDK won't break when Eskiz
    adds new ones); access the raw response via ``client.sms.status(...)``
    error paths or the underlying ``RawResponse`` if you need them.
    """

    id: int | None = None
    user_id: int | None = None
    country_id: int | None = None
    connection_id: int | None = None
    smsc_id: int | None = None
    dispatch_id: int | None = None
    user_sms_id: str | None = None
    request_id: str | None = None
    price: float | None = None
    total_price: float | None = None
    is_ad: bool | None = None
    nick: str | None = None
    to: str | None = None
    message: str | None = None
    encoding: int | None = None
    parts_count: int | None = None

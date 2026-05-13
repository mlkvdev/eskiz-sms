"""Pydantic models for Eskiz API requests and responses.

All models accept (but ignore) unknown fields so server additions don't
break the SDK. Phone numbers are normalized to digits-only on input.
"""

from eskiz.models.reports import (
    DispatchExpense,
    LimitInfo,
    LocalPriceEntry,
    PriceEntry,
    PriceList,
    RangeExpense,
    SmscTotal,
    Total,
    TotalByMonth,
)
from eskiz.models.sms import (
    BatchMessage,
    BatchSendResult,
    DispatchStatusRow,
    NormalizerCharacter,
    PaginatedMessages,
    SendResult,
    SmsCheckInfo,
    SmsCheckResult,
    SmsLogEntry,
    SmsLogResponse,
    SmsStatusDetail,
)
from eskiz.models.templates import (
    Template,
    TemplateCreated,
    TemplateList,
)
from eskiz.models.user import User

__all__ = [
    "BatchMessage",
    "BatchSendResult",
    "DispatchExpense",
    "DispatchStatusRow",
    "LimitInfo",
    "LocalPriceEntry",
    "NormalizerCharacter",
    "PaginatedMessages",
    "PriceEntry",
    "PriceList",
    "RangeExpense",
    "SendResult",
    "SmsCheckInfo",
    "SmsCheckResult",
    "SmsLogEntry",
    "SmsLogResponse",
    "SmsStatusDetail",
    "SmscTotal",
    "Template",
    "TemplateCreated",
    "TemplateList",
    "Total",
    "TotalByMonth",
    "User",
]

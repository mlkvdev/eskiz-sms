"""Endpoint paths in one place — sourced from the official Eskiz Postman collection."""

from __future__ import annotations

from typing import Final

# ----- auth -----
LOGIN: Final = "/auth/login"
REFRESH: Final = "/auth/refresh"
ME: Final = "/auth/user"

# ----- templates -----
TEMPLATE_CREATE: Final = "/user/template"
TEMPLATES_LIST: Final = "/user/templates"

# ----- sms send -----
SEND_SMS: Final = "/message/sms/send"
SEND_BATCH_SMS: Final = "/message/sms/send-batch"
SEND_GLOBAL_SMS: Final = "/message/sms/send-global"

# ----- sms query -----
USER_MESSAGES: Final = "/message/sms/get-user-messages"
USER_MESSAGES_BY_DISPATCH: Final = "/message/sms/get-user-messages-by-dispatch"
DISPATCH_STATUS: Final = "/message/sms/get-dispatch-status"


def sms_status_by_id(sms_id: str | int) -> str:
    return f"/message/sms/status_by_id/{sms_id}"


# ----- sms utilities -----
NICK_ME: Final = "/nick/me"
SMS_NORMALIZER: Final = "/message/sms/normalizer"
SMS_CHECK: Final = "/message/sms/check"

# ----- reports -----
USER_TOTALS: Final = "/user/totals"
USER_LIMIT: Final = "/user/get-limit"
USER_PRICES: Final = "/user/prices"
MESSAGE_EXPORT: Final = "/message/export"
REPORT_TOTAL_BY_MONTH: Final = "/report/total-by-month"
REPORT_TOTAL_BY_SMSC: Final = "/report/total-by-smsc"
REPORT_TOTAL_BY_RANGE: Final = "/report/total-by-range"
REPORT_TOTAL_BY_DISPATCH: Final = "/report/total-by-dispatch"


def sms_log(sms_id: str | int) -> str:
    return f"/logs/sms/{sms_id}"

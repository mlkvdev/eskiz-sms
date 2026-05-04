"""Resource classes — public surface area, namespaced by domain."""

from eskiz.resources.auth import AsyncAuthResource, AuthResource
from eskiz.resources.reports import AsyncReportsResource, ReportsResource
from eskiz.resources.sms import AsyncSmsResource, SmsResource
from eskiz.resources.templates import AsyncTemplatesResource, TemplatesResource

__all__ = [
    "AsyncAuthResource",
    "AsyncReportsResource",
    "AsyncSmsResource",
    "AsyncTemplatesResource",
    "AuthResource",
    "ReportsResource",
    "SmsResource",
    "TemplatesResource",
]

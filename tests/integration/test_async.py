"""Async parity smokes — same read-only calls via AsyncEskizSMS.

If the sync suite passes but these don't, the async transport layer has
diverged from the sync one.
"""

from __future__ import annotations

import pytest

from eskiz import AsyncEskizSMS
from eskiz.models import LimitInfo, SmsCheckResult, User

pytestmark = pytest.mark.integration


async def test_async_auth_me(live_aclient: AsyncEskizSMS) -> None:
    user = await live_aclient.auth.me()

    assert isinstance(user, User)
    assert user.id > 0


async def test_async_reports_balance(live_aclient: AsyncEskizSMS) -> None:
    info = await live_aclient.reports.balance()

    assert isinstance(info, LimitInfo)
    assert info.balance >= 0


async def test_async_sms_check(live_aclient: AsyncEskizSMS) -> None:
    result = await live_aclient.sms.check("Bu test xabaridir")

    assert isinstance(result, SmsCheckResult)
    assert len(result.info) > 0


async def test_async_sms_nicks(live_aclient: AsyncEskizSMS) -> None:
    nicks = await live_aclient.sms.nicks()

    assert isinstance(nicks, list)

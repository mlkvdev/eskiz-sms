"""Read-only smoke tests against the live Eskiz API.

Each test issues a single GET (or otherwise side-effect-free POST) and asserts
the response parses into the typed model. These should not consume credits.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from eskiz import EskizSMS
from eskiz.models import LimitInfo, PriceList, SmsCheckResult, TemplateList, User

pytestmark = pytest.mark.integration


def test_auth_me(live_client: EskizSMS) -> None:
    user = live_client.auth.me()

    assert isinstance(user, User)
    assert user.id > 0
    assert "@" in user.email


def test_reports_balance(live_client: EskizSMS) -> None:
    info = live_client.reports.balance()

    assert isinstance(info, LimitInfo)
    assert info.balance >= 0


def test_reports_prices(live_client: EskizSMS) -> None:
    prices = live_client.reports.prices()

    assert isinstance(prices, PriceList)
    # at least one of the two lists should be populated
    assert (prices.global_ and len(prices.global_) > 0) or (
        prices.local and len(prices.local) > 0
    )


def test_reports_totals_current_month(live_client: EskizSMS) -> None:
    now = datetime.now()
    rows = live_client.reports.totals(year=now.year, month=now.month)

    # may legitimately be empty for new accounts; just shape-check
    assert isinstance(rows, list)


def test_sms_nicks(live_client: EskizSMS) -> None:
    nicks = live_client.sms.nicks()

    assert isinstance(nicks, list)
    # most accounts at minimum have the default 4546 alphanumeric
    assert all(isinstance(n, str) for n in nicks)


def test_sms_check(live_client: EskizSMS) -> None:
    result = live_client.sms.check("Bu test xabaridir")

    assert isinstance(result, SmsCheckResult)
    assert len(result.info) > 0


def test_sms_normalize(live_client: EskizSMS) -> None:
    # ASCII-only input should produce zero flagged characters
    chars = live_client.sms.normalize("hello world")

    assert isinstance(chars, list)
    assert chars == []


def test_templates_list(live_client: EskizSMS) -> None:
    templates = live_client.templates.list_all()

    assert isinstance(templates, TemplateList)
    assert templates.success is True

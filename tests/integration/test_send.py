"""Live SMS send — costs credits.

Doubly gated: ``--run-integration`` is required to collect, and the
``test_phone`` fixture skips unless ``ESKIZ_TEST_PHONE`` is set in the
environment. The body uses Eskiz's standard test template so unverified
accounts can still send.
"""

from __future__ import annotations

import time

import pytest

from eskiz import EskizSMS
from eskiz.models import SendResult, SmsStatusDetail

pytestmark = pytest.mark.integration

# Eskiz test sender + body that is always allowed without template approval.
TEST_FROM = "4546"
TEST_BODY = "Bu Eskiz dan test"


def test_send_and_status_roundtrip(live_client: EskizSMS, test_phone: str) -> None:
    result = live_client.sms.send(
        mobile_phone=test_phone,
        message=TEST_BODY,
        from_whom=TEST_FROM,
    )

    assert isinstance(result, SendResult)
    assert result.id is not None
    assert result.status in {"waiting", "Waiting"}

    # Give Eskiz a moment to materialise the message before fetching status.
    time.sleep(2)

    detail = live_client.sms.status(result.id)
    assert isinstance(detail, SmsStatusDetail)
    assert detail.id is not None

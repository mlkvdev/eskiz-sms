"""Live SMS send — costs credits.

Doubly gated: ``--run-integration`` is required to collect, and the
``test_phone`` fixture skips unless ``ESKIZ_TEST_PHONE`` is set in the
environment.

Eskiz moderates SMS bodies per-account. If the default ``Eskiz Test`` text
hasn't been approved on this account, the test will skip with guidance —
set ``ESKIZ_TEST_BODY`` to a body you've approved via my.eskiz.uz.
"""

from __future__ import annotations

import os
import time

import pytest

from eskiz import EskizSMS
from eskiz.exceptions import EskizBadRequest
from eskiz.models import SendResult, SmsStatusDetail

pytestmark = pytest.mark.integration

TEST_FROM = "4546"
DEFAULT_BODY = "Eskiz Test"
STATUS_POLL_ATTEMPTS = 4
STATUS_POLL_INTERVAL = 2.0


def test_send_and_status_roundtrip(live_client: EskizSMS, test_phone: str) -> None:
    body = os.environ.get("ESKIZ_TEST_BODY", DEFAULT_BODY)

    try:
        result = live_client.sms.send(
            mobile_phone=test_phone,
            message=body,
            from_whom=TEST_FROM,
        )
    except EskizBadRequest as exc:
        if "модерац" in str(exc).lower() or "moderation" in str(exc).lower():
            pytest.skip(
                f"Body {body!r} is not pre-approved on this account; "
                "set ESKIZ_TEST_BODY to an approved template."
            )
        raise

    assert isinstance(result, SendResult)
    assert result.id is not None
    assert result.status in {"waiting", "Waiting"}

    # Eskiz needs a moment to materialise the message; poll a few times
    # rather than sleeping a fixed window so the happy path is fast and
    # slow days don't flake the test.
    detail: SmsStatusDetail | None = None
    last_exc: EskizBadRequest | None = None
    for _ in range(STATUS_POLL_ATTEMPTS):
        time.sleep(STATUS_POLL_INTERVAL)
        try:
            detail = live_client.sms.status(result.id)
            break
        except EskizBadRequest as exc:
            last_exc = exc
            continue

    if detail is None:
        raise AssertionError(
            f"sms.status never returned a row after "
            f"{STATUS_POLL_ATTEMPTS * STATUS_POLL_INTERVAL}s"
        ) from last_exc
    assert isinstance(detail, SmsStatusDetail)
    assert detail.id is not None

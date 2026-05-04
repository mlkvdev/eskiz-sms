"""Round-trip smoke tests for each resource — validates wire format + parsing."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from eskiz import EskizSMS

from ._helpers import BASE_URL, mock_login


def test_sms_send_form_encoded_request(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock)
        send = mock.post(f"{BASE_URL}/message/sms/send").mock(
            return_value=Response(
                200, json={"id": "abc-123", "message": "Waiting", "status": "waiting"}
            )
        )

        result = client.sms.send(mobile_phone="+998 99 123 45 67", message="hi", from_whom="4546")

        assert result.id == "abc-123"
        assert result.status == "waiting"
        request = send.calls[0].request
        body = request.content.decode()
        # form-encoded; phone should be normalized (no spaces, no +)
        assert "mobile_phone=998991234567" in body
        assert "message=hi" in body
        assert "from=4546" in body


def test_sms_send_batch_uses_json(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock)
        batch = mock.post(f"{BASE_URL}/message/sms/send-batch").mock(
            return_value=Response(
                200, json={"id": "b-1", "message": "Waiting", "status": ["waiting", "waiting"]}
            )
        )

        result = client.sms.send_batch(
            messages=[
                {"user_sms_id": "s1", "to": 998990000000, "text": "x"},
                {"user_sms_id": "s2", "to": "998980000000", "text": "y"},
            ],
            dispatch_id=42,
        )

        assert result.status == ["waiting", "waiting"]
        request = batch.calls[0].request
        assert request.headers["content-type"].startswith("application/json")
        # ints in `to` are stringified by the protocol layer
        assert b'"to":"998990000000"' in request.content
        assert b'"dispatch_id":42' in request.content


def test_sms_send_callback_default_from_config() -> None:
    from eskiz import Config

    cfg = Config(
        email="u@e.com",
        password="p",
        base_url=BASE_URL,
        callback_url="https://example.com/cb",
    )
    with respx.mock() as mock, EskizSMS(cfg) as client:
        mock_login(mock)
        send = mock.post(f"{BASE_URL}/message/sms/send").mock(
            return_value=Response(200, json={"id": "x", "status": "waiting"})
        )

        client.sms.send(mobile_phone="998991234567", message="hi")

        body = send.calls[0].request.content.decode()
        assert "callback_url=https" in body  # url-encoded; just sanity-check prefix


def test_sms_dispatch_status_typed_rows(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock)
        mock.post(f"{BASE_URL}/message/sms/get-dispatch-status").mock(
            return_value=Response(
                200,
                json={
                    "status": "success",
                    "data": [
                        {"status": "DELIVERED", "total": 18},
                        {"status": "REJECTED", "total": 2},
                    ],
                },
            )
        )

        rows = client.sms.dispatch_status(dispatch_id=123, user_id=1)
        assert len(rows) == 2
        assert rows[0].status == "DELIVERED"
        assert rows[0].total == 18


def test_reports_balance(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/user/get-limit").mock(
            return_value=Response(200, json={"status": "success", "data": {"balance": 12500}})
        )

        info = client.reports.balance()
        assert info.balance == 12500


def test_reports_by_month_typed(client: EskizSMS) -> None:
    """H4: by_month should return typed TotalByMonth rows, not raw dicts."""
    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/report/total-by-month").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "year": 2026,
                            "month": 5,
                            "ad_parts": 14,
                            "ad_spent": 1610,
                            "parts": 409,
                            "spent": 22594,
                            "total_parts": 423,
                            "total_spent": 24204,
                        }
                    ]
                },
            )
        )

        rows = client.reports.by_month(2026)
        assert len(rows) == 1
        assert rows[0].year == 2026 and rows[0].month == 5
        assert rows[0].total_spent == 24204


def test_templates_list_all(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/user/templates").mock(
            return_value=Response(
                200,
                json={
                    "success": True,
                    "result": [
                        {
                            "id": 1,
                            "template": "tpl",
                            "original_text": "Hi",
                            "status": "moderation",
                        }
                    ],
                },
            )
        )

        result = client.templates.list_all()
        assert result.success is True
        assert len(result.result) == 1
        assert result.result[0].id == 1


def test_validation_error_wrapped_as_bad_request(client: EskizSMS) -> None:
    """H5: pydantic.ValidationError must be re-raised as BadRequest, not leak."""
    from eskiz import BadRequest

    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200,
                # Missing required `id` field — pydantic will reject it.
                json={"status": "success", "data": {"email": "u@e.com"}},
            )
        )

        with pytest.raises(BadRequest):
            client.auth.me()


def test_invalid_callback_url_raises_validation_error(client: EskizSMS) -> None:
    from eskiz import ValidationError

    with pytest.raises(ValidationError):
        client.sms.send(mobile_phone="998991234567", message="hi", callback_url="not a url")

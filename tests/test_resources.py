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
    with (
        respx.mock() as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            callback_url="https://example.com/cb",
        ) as client,
    ):
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
    """H5: pydantic.ValidationError must be re-raised as EskizBadRequest, not leak."""
    from eskiz import EskizBadRequest

    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200,
                # Missing required `id` field — pydantic will reject it.
                json={"status": "success", "data": {"email": "u@e.com"}},
            )
        )

        with pytest.raises(EskizBadRequest):
            client.auth.me()


def test_invalid_callback_url_raises_validation_error(client: EskizSMS) -> None:
    from eskiz import EskizValidationError

    with pytest.raises(EskizValidationError):
        client.sms.send(mobile_phone="998991234567", message="hi", callback_url="not a url")


def test_http_callback_url_rejected_by_default(client: EskizSMS) -> None:
    """Plain http:// callbacks must be rejected unless the client opts in."""
    from eskiz import EskizValidationError

    with pytest.raises(EskizValidationError, match="https"):
        client.sms.send(
            mobile_phone="998991234567", message="hi", callback_url="http://example.com/cb"
        )


def test_http_callback_url_allowed_with_opt_in() -> None:
    """allow_insecure_callback=True permits http:// (for staging/local use)."""
    with (
        respx.mock() as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            allow_insecure_callback=True,
        ) as client,
    ):
        mock_login(mock)
        send = mock.post(f"{BASE_URL}/message/sms/send").mock(
            return_value=Response(200, json={"id": "x", "status": "waiting"})
        )

        client.sms.send(
            mobile_phone="998991234567",
            message="hi",
            from_whom="4546",
            callback_url="http://example.com/cb",
        )

        body = send.calls[0].request.content.decode()
        assert "callback_url=http%3A" in body


def test_batch_message_missing_to_raises_validation_error(client: EskizSMS) -> None:
    """Local validation: missing 'to' key in a batch dict surfaces clearly."""
    from eskiz import EskizValidationError

    with pytest.raises(EskizValidationError, match="'to'"):
        client.sms.send_batch(
            messages=[{"user_sms_id": "s1", "text": "x"}],  # type: ignore[typeddict-item]
            dispatch_id=42,
        )


def test_network_error_surfaces_as_eskiz_http_error(client: EskizSMS) -> None:
    """A transport-level failure must wrap into EskizHTTPError, not leak httpx."""
    import httpx

    from eskiz import EskizHTTPError

    with respx.mock() as mock:
        mock_login(mock)
        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=httpx.ConnectError("boom"))

        with pytest.raises(EskizHTTPError):
            client.auth.me()


def test_safe_method_retries_on_5xx() -> None:
    """A 500 on a GET must be retried up to max_retries times."""
    with (
        respx.mock() as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            max_retries=2,
        ) as client,
    ):
        mock_login(mock)
        responses = [
            Response(500, json={"message": "server error"}),
            Response(500, json={"message": "server error"}),
            Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}}),
        ]
        me = mock.get(f"{BASE_URL}/auth/user").mock(side_effect=responses)

        user = client.auth.me()
        assert user.id == 1
        assert me.call_count == 3


def test_unsafe_method_does_not_retry_on_5xx() -> None:
    """A 500 on POST must not be retried by the SDK loop, even with max_retries set."""
    from eskiz import EskizBadRequest

    with (
        respx.mock() as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            max_retries=3,
        ) as client,
    ):
        mock_login(mock)
        send = mock.post(f"{BASE_URL}/message/sms/send").mock(
            return_value=Response(500, json={"message": "server error"})
        )

        with pytest.raises(EskizBadRequest):
            client.sms.send(mobile_phone="998991234567", message="hi", from_whom="4546")
        assert send.call_count == 1, "POST 500 should not be retried in the SDK loop"

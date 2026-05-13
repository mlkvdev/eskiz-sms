"""Auth flow: login, token refresh, error mapping."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from eskiz import AsyncEskizSMS, EskizSMS, InvalidCredentials, TokenInvalid
from eskiz.config import Config

from ._helpers import BASE_URL, mock_login, mock_refresh


def test_login_caches_token(client: EskizSMS) -> None:
    with respx.mock(assert_all_called=False) as mock:
        login = mock_login(mock, token="abc")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(
                200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}}
            )
        )

        client.auth.me()
        client.auth.me()  # second call should reuse the cached token

        assert login.call_count == 1, "login should be invoked exactly once"


def test_login_invalid_credentials_raises_invalid_credentials(client: EskizSMS) -> None:
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/auth/login").mock(
            return_value=Response(401, json={"message": "Invalid credentials", "status": "error"})
        )
        with pytest.raises(InvalidCredentials):
            client.auth.me()


def test_login_401_with_unfamiliar_message_still_raises_invalid_credentials(
    client: EskizSMS,
) -> None:
    """C2: any 401 on /auth/login should map to InvalidCredentials."""
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/auth/login").mock(
            return_value=Response(401, json={"message": "Login failed somehow"})
        )
        with pytest.raises(InvalidCredentials):
            client.auth.me()


def test_token_refresh_on_expired(client: EskizSMS) -> None:
    """When a request returns 401, we PATCH /auth/refresh and retry once."""
    with respx.mock() as mock:
        mock_login(mock, token="t1")
        refresh = mock_refresh(mock, token="t2")

        seen_tokens: list[str] = []

        def me_handler(request):
            auth = request.headers.get("authorization", "")
            seen_tokens.append(auth)
            if auth == "Bearer t1":
                return Response(401, json={"message": "Expired Token"})
            return Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}})

        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=me_handler)

        user = client.auth.me()
        assert user.id == 1
        assert refresh.call_count == 1
        assert seen_tokens == ["Bearer t1", "Bearer t2"]


def test_refresh_falls_back_to_login_on_auth_error(client: EskizSMS) -> None:
    """If /auth/refresh itself returns 401, the token manager re-logs-in."""
    with respx.mock() as mock:
        login_call_count = 0

        def login_handler(request):
            nonlocal login_call_count
            login_call_count += 1
            tok = f"t{login_call_count}"
            return Response(200, json={"message": "ok", "data": {"token": tok}})

        mock.post(f"{BASE_URL}/auth/login").mock(side_effect=login_handler)
        mock.patch(f"{BASE_URL}/auth/refresh").mock(
            return_value=Response(401, json={"message": "Expired Token"})
        )

        seen: list[str] = []

        def me_handler(request):
            auth = request.headers.get("authorization", "")
            seen.append(auth)
            if auth == "Bearer t1":
                return Response(401, json={"message": "Expired Token"})
            return Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}})

        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=me_handler)

        user = client.auth.me()
        assert user.id == 1
        assert login_call_count == 2  # initial login + fallback after refresh failed
        assert seen == ["Bearer t1", "Bearer t2"]


def test_post_refresh_invalid_token_raises_token_invalid(client: EskizSMS) -> None:
    """H6: if the refreshed token is itself rejected, raise TokenInvalid (not TokenExpired)."""
    with respx.mock() as mock:
        mock_login(mock, token="t1")
        mock_refresh(mock, token="t2")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(401, json={"message": "Expired Token"})
        )

        with pytest.raises(TokenInvalid):
            client.auth.me()


def test_token_invalid_status_skips_refresh(client: EskizSMS) -> None:
    """C3: a 401 with status=token_invalid should NOT trigger a refresh."""
    with respx.mock(assert_all_called=False) as mock:
        mock_login(mock, token="t1")
        refresh = mock_refresh(mock, token="t2")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(401, json={"status": "token_invalid", "message": "no"})
        )

        from eskiz import TokenInvalid as TI

        with pytest.raises(TI):
            client.auth.me()
        assert refresh.call_count == 0


@pytest.mark.asyncio
async def test_async_login_and_refresh(aclient: AsyncEskizSMS) -> None:
    with respx.mock() as mock:
        mock_login(mock, token="t1")
        refresh = mock_refresh(mock, token="t2")

        def me_handler(request):
            if request.headers.get("authorization") == "Bearer t1":
                return Response(401, json={"message": "Expired"})
            return Response(200, json={"status": "success", "data": {"id": 1, "email": "u@e.com"}})

        mock.get(f"{BASE_URL}/auth/user").mock(side_effect=me_handler)

        user = await aclient.auth.me()
        assert user.id == 1
        assert refresh.call_count == 1


def test_password_not_in_config_repr() -> None:
    """C1: password must be redacted from repr/str of the internal config."""
    cfg = Config(email="a@b.c", password="super-secret")
    assert "super-secret" not in repr(cfg)
    assert "super-secret" not in str(cfg)


def test_login_token_invalid_status_also_maps_to_invalid_credentials(client: EskizSMS) -> None:
    """A 401 on /auth/login with status=token_invalid must surface as InvalidCredentials."""
    with respx.mock() as mock:
        mock.post(f"{BASE_URL}/auth/login").mock(
            return_value=Response(
                401, json={"status": "token_invalid", "message": "bad credentials"}
            )
        )
        with pytest.raises(InvalidCredentials):
            client.auth.me()


def test_non_401_with_invalid_credentials_message_is_not_misclassified(
    client: EskizSMS,
) -> None:
    """A 500 carrying 'Invalid credentials' must not be turned into InvalidCredentials."""
    from eskiz import EskizBadRequest

    with respx.mock() as mock:
        mock_login(mock, token="t1")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(500, json={"message": "Invalid credentials"})
        )
        with pytest.raises(EskizBadRequest) as exc_info:
            client.auth.me()
        assert not isinstance(exc_info.value, InvalidCredentials)


def test_enable_token_refresh_false_raises_token_expired_without_refresh() -> None:
    """When the flag is off, a 401 mid-session bubbles up as TokenExpired without refresh."""
    from eskiz import TokenExpired

    with (
        respx.mock(assert_all_called=False) as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            enable_token_refresh=False,
        ) as client,
    ):
        mock_login(mock, token="t1")
        refresh = mock_refresh(mock, token="t2")
        mock.get(f"{BASE_URL}/auth/user").mock(
            return_value=Response(401, json={"message": "Expired Token"})
        )

        with pytest.raises(TokenExpired):
            client.auth.me()
        assert refresh.call_count == 0, "refresh must not be called when the flag is off"


def test_refresh_after_failure_short_circuits_when_storage_has_newer_token() -> None:
    """If a peer refreshed first, refresh_after_failure must reuse the new token."""
    from eskiz import MemoryTokenStorage

    storage = MemoryTokenStorage(initial="stale")
    with (
        respx.mock(assert_all_called=False) as mock,
        EskizSMS(
            email="u@e.com",
            password="p",
            base_url=BASE_URL,
            token_storage=storage,
        ) as client,
    ):
        refresh = mock_refresh(mock, token="never-used")

        # Simulate concurrent peer: stash a fresh token in storage before
        # the manager's refresh path runs.
        storage.set("fresh")
        new_token = client._tokens.refresh_after_failure("stale")  # type: ignore[attr-defined]

        assert new_token == "fresh"
        assert refresh.call_count == 0

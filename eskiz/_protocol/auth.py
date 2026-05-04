"""Auth protocol — login, refresh, current user."""

from __future__ import annotations

from eskiz import endpoints as ep
from eskiz._protocol import RequestPlan
from eskiz._protocol._helpers import envelope_data, extract_token
from eskiz.models import User


def login(email: str, password: str) -> RequestPlan[str]:
    return RequestPlan(
        method="POST",
        path=ep.LOGIN,
        data={"email": email, "password": password},
        parse=extract_token,
    )


def refresh() -> RequestPlan[str]:
    return RequestPlan(method="PATCH", path=ep.REFRESH, parse=extract_token)


def me() -> RequestPlan[User]:
    return RequestPlan(
        method="GET",
        path=ep.ME,
        parse=lambda r: User.model_validate(envelope_data(r.data)),
    )

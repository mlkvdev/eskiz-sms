"""User model."""

from __future__ import annotations

from datetime import datetime

from eskiz.models.common import BaseEskizModel


class User(BaseEskizModel):
    """Authenticated user info from ``/auth/user``.

    Note: the API returns a ``password`` field (often empty) and other
    sensitive metadata; we deliberately surface only what's safe and stable.
    """

    id: int
    email: str
    name: str | None = None
    role: str | None = None
    status: str | None = None
    is_vip: bool | None = None
    balance: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

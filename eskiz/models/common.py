"""Shared model primitives."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    """Base model — ignore unknown fields, populate by name or alias."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class EnvelopeStatus(StrEnum):
    """Top-level ``status`` field returned by Eskiz responses."""

    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"


class ResponseEnvelope(_Base):
    """The standard ``{status, message, data}`` wrapper Eskiz returns."""

    status: EnvelopeStatus | str | None = None
    message: str | None = None
    data: Any = None

"""Shared model primitives."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseEskizModel(BaseModel):
    """Base model — ignore unknown fields, populate by name or alias."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

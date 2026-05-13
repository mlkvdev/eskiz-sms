"""Template models."""

from __future__ import annotations

from eskiz.models.common import BaseEskizModel


class Template(BaseEskizModel):
    """SMS template record from ``/user/templates``."""

    id: int
    template: str | None = None
    original_text: str | None = None
    status: str | None = None


class TemplateCreated(BaseEskizModel):
    """Response from ``POST /user/template`` — bare ``{template}``."""

    template: str


class TemplateList(BaseEskizModel):
    """``GET /user/templates`` response shape."""

    success: bool
    result: list[Template]

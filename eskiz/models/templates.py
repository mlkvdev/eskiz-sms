"""Template models."""

from __future__ import annotations

from eskiz.models.common import _Base


class Template(_Base):
    """SMS template record from ``/user/templates``."""

    id: int
    template: str | None = None
    original_text: str | None = None
    status: str | None = None


class TemplateCreated(_Base):
    """Response from ``POST /user/template`` — bare ``{template}``."""

    template: str


class TemplateList(_Base):
    """``GET /user/templates`` response shape."""

    success: bool
    result: list[Template]

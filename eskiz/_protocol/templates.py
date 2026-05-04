"""Templates protocol — create, list."""

from __future__ import annotations

from eskiz import endpoints as ep
from eskiz._protocol import RequestPlan
from eskiz.models import TemplateCreated, TemplateList


def create(template: str) -> RequestPlan[TemplateCreated]:
    return RequestPlan(
        method="POST",
        path=ep.TEMPLATE_CREATE,
        data={"template": template},
        parse=lambda r: TemplateCreated.model_validate(r.data),
    )


def list_() -> RequestPlan[TemplateList]:
    return RequestPlan(
        method="GET",
        path=ep.TEMPLATES_LIST,
        parse=lambda r: TemplateList.model_validate(r.data),
    )

"""Templates protocol — create, list."""

from __future__ import annotations

from eskiz import endpoints as ep
from eskiz._protocol import RequestPlan
from eskiz._protocol._helpers import unexpected_shape
from eskiz.models import TemplateCreated, TemplateList
from eskiz.transport.base import RawResponse


def create(template: str) -> RequestPlan[TemplateCreated]:
    def parse(r: RawResponse) -> TemplateCreated:
        if not isinstance(r.data, dict):
            raise unexpected_shape(r.data, status_code=r.status_code)
        return TemplateCreated.model_validate(r.data)

    return RequestPlan(
        method="POST",
        path=ep.TEMPLATE_CREATE,
        data={"template": template},
        parse=parse,
    )


def list_() -> RequestPlan[TemplateList]:
    def parse(r: RawResponse) -> TemplateList:
        if not isinstance(r.data, dict):
            raise unexpected_shape(r.data, status_code=r.status_code)
        return TemplateList.model_validate(r.data)

    return RequestPlan(
        method="GET",
        path=ep.TEMPLATES_LIST,
        parse=parse,
    )

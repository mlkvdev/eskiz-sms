"""Report and limit/pricing models."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from eskiz.models.common import BaseEskizModel


class LimitInfo(BaseEskizModel):
    """``/user/get-limit`` response — current balance."""

    balance: float


class Total(BaseEskizModel):
    """One row from ``/user/totals``."""

    status: str
    month: str
    packets: int


class TotalByMonth(BaseEskizModel):
    """One row from ``/report/total-by-month``."""

    year: int
    month: int
    ad_parts: int = 0
    ad_spent: int = 0
    parts: int = 0
    spent: int = 0
    total_parts: int = 0
    total_spent: int = 0


class SmscTotal(TotalByMonth):
    """One row from ``/report/total-by-smsc``."""

    smsc_id: int


class RangeExpense(BaseEskizModel):
    """One row from ``/report/total-by-range``."""

    start_date: date | datetime | str | None = None
    to_date: date | datetime | str | None = None
    parts: int | None = None
    spent: int | None = None
    total_parts: int | None = None
    total_spent: int | None = None


class DispatchExpense(BaseEskizModel):
    """One row from ``/report/total-by-dispatch``."""

    dispatch_id: int
    parts: int | None = None
    spent: int | None = None


class PriceEntry(BaseEskizModel):
    """One country in the global pricing list."""

    code: str
    name: str
    prefix: str
    status: str
    price: int | float


class LocalPriceEntry(BaseEskizModel):
    """One SMSC entry in the local pricing list.

    Local rows have a different shape than global ones — they are keyed by
    SMSC id and carry both regular and ad-rate prices.
    """

    smsc_id: int
    name: str
    price: int | float
    ad_price: int | float | None = None


class PriceList(BaseEskizModel):
    """``/user/prices`` response."""

    global_: list[PriceEntry] | None = Field(default=None, alias="global")
    local: list[LocalPriceEntry] | None = None

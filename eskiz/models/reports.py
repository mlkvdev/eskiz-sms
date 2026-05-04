"""Report and limit/pricing models."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from eskiz.models.common import _Base


class LimitInfo(_Base):
    """``/user/get-limit`` response — current balance."""

    balance: float


class Total(_Base):
    """One row from ``/user/totals``."""

    status: str
    month: str
    packets: int


class TotalByMonth(_Base):
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


class RangeExpense(_Base):
    """One row from ``/report/total-by-range``."""

    start_date: date | datetime | str | None = None
    to_date: date | datetime | str | None = None
    parts: int | None = None
    spent: int | None = None
    total_parts: int | None = None
    total_spent: int | None = None


class DispatchExpense(_Base):
    """One row from ``/report/total-by-dispatch``."""

    dispatch_id: int
    parts: int | None = None
    spent: int | None = None


class PriceEntry(_Base):
    """One country in the global pricing list."""

    code: str
    name: str
    prefix: str
    status: str
    price: int | float


class LocalPriceEntry(_Base):
    """One SMSC entry in the local pricing list.

    Local rows have a different shape than global ones — they are keyed by
    SMSC id and carry both regular and ad-rate prices.
    """

    smsc_id: int
    name: str
    price: int | float
    ad_price: int | float | None = None


class PriceList(_Base):
    """``/user/prices`` response."""

    global_: list[PriceEntry] | None = Field(default=None, alias="global")
    local: list[LocalPriceEntry] | None = None

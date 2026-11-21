"""Monetary types. All arithmetic uses Decimal. Rounding is explicit."""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from spendlens.domain.enums import AttributionLevel, CostMetric


class Quantities:
    """Documented rounding policy.

    Internal rates: 6 decimal places.
    Internal money: 4 decimal places (tenths of a mill).
    Presentation / reports: 2 decimal places, banker's rounding (ROUND_HALF_EVEN).
    Rounding is applied only at presentation or ledger-posting boundaries, never
    inside intermediate formula steps.
    """

    RATE = Decimal("0.000001")
    MONEY = Decimal("0.0001")
    PRESENTATION = Decimal("0.01")
    PERCENT = Decimal("0.01")

    @staticmethod
    def d(value: Decimal | int | str | float) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, float):
            raise TypeError("float is not allowed for monetary values; use Decimal or str")
        return Decimal(value)

    @classmethod
    def q_rate(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.RATE, rounding=ROUND_HALF_EVEN)

    @classmethod
    def q_money(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.MONEY, rounding=ROUND_HALF_EVEN)

    @classmethod
    def q_present(cls, value: Decimal) -> Decimal:
        return value.quantize(cls.PRESENTATION, rounding=ROUND_HALF_EVEN)


class Money(BaseModel):
    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: str = Field(min_length=3, max_length=3)
    metric: CostMetric = CostMetric.UNBLENDED
    estimated: bool = True
    attribution: AttributionLevel = AttributionLevel.RESOURCE

    @field_validator("currency")
    @classmethod
    def upper_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator("amount")
    @classmethod
    def no_float(cls, v: Decimal | int | str) -> Decimal:
        return Quantities.d(v)

    def present(self) -> Decimal:
        return Quantities.q_present(self.amount)

    def add(self, other: Money) -> Money:
        self._same_basis(other)
        return self.model_copy(update={"amount": self.amount + other.amount})

    def sub(self, other: Money) -> Money:
        self._same_basis(other)
        return self.model_copy(update={"amount": self.amount - other.amount})

    def _same_basis(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"cannot combine currencies {self.currency} and {other.currency} "
                "without an explicit dated exchange rate"
            )
        if self.metric != other.metric:
            raise ValueError(
                f"cannot mix cost metrics {self.metric} and {other.metric}; "
                "use a single basis consistently"
            )

    @classmethod
    def zero(cls, currency: str = "USD", metric: CostMetric = CostMetric.UNBLENDED) -> Self:
        return cls(amount=Decimal("0"), currency=currency, metric=metric, estimated=False)

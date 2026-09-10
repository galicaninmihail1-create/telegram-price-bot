from decimal import ROUND_HALF_UP, Decimal

from app.domain.models import PriceResult


class PriceCalculator:
    def __init__(self, markup_percent: Decimal, fixed_markup_byn: Decimal, rounding: Decimal) -> None:
        if rounding <= 0:
            raise ValueError("rounding must be positive")
        self.markup_percent = markup_percent
        self.fixed_markup_byn = fixed_markup_byn
        self.rounding = rounding

    def calculate(self, price_rub: Decimal, rub_to_byn_rate: Decimal) -> PriceResult:
        base = price_rub * rub_to_byn_rate
        unrounded = base * (Decimal("1") + self.markup_percent / Decimal("100")) + self.fixed_markup_byn
        final = (unrounded / self.rounding).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * self.rounding
        return PriceResult(base_price_byn=base, final_price_byn=final)

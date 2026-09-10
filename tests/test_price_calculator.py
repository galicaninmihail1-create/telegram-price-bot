from decimal import Decimal

from app.services.price_calculator import PriceCalculator


def test_rate_markup_fixed_markup_and_rounding() -> None:
    calculator = PriceCalculator(Decimal("10"), Decimal("5"), Decimal("1"))
    result = calculator.calculate(Decimal("3500"), Decimal("0.0305"))
    assert result.base_price_byn == Decimal("106.7500")
    assert result.final_price_byn == Decimal("122")


def test_custom_rounding_step() -> None:
    calculator = PriceCalculator(Decimal("0"), Decimal("0"), Decimal("5"))
    assert calculator.calculate(Decimal("101"), Decimal("1")).final_price_byn == Decimal("100")

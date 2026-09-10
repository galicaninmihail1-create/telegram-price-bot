import sys
from decimal import Decimal

from app.bot.formatting import format_post
from app.services.price_calculator import PriceCalculator
from app.utils.parsing import parse_caption


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    caption = "Кроссовки женские 3500"
    rate = Decimal("0.035")
    parsed = parse_caption(caption)
    result = PriceCalculator(Decimal("0"), Decimal("0"), Decimal("1")).calculate(
        parsed.price_rub,
        rate,
    )
    print(f"Вход: {caption}")
    print(f"Курс: {rate} BYN за 1 RUB")
    print(f"Базовая цена: {result.base_price_byn} BYN")
    print(f"Итоговая цена: {result.final_price_byn} BYN")
    print("\nГотовый пост:\n")
    print(format_post(parsed.category, result.final_price_byn))


if __name__ == "__main__":
    main()

from decimal import Decimal

from app.bot.formatting import format_post


def test_format_post() -> None:
    assert format_post("Кроссовки женские", Decimal("125")) == (
        "👟 Кроссовки женские\n\n"
        "💰 Цена: 125 BYN\n\n"
        "Для заказа пишите в личные сообщения."
    )


def test_format_post_removes_insignificant_decimal_zeroes() -> None:
    assert "Цена: 125.5 BYN" in format_post("Товар", Decimal("125.50"))

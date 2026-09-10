from decimal import Decimal

import pytest

from app.utils.parsing import CaptionParseError, parse_caption


@pytest.mark.parametrize(
    ("caption", "category", "price"),
    [
        ("Кроссовки женские 3500", "Кроссовки женские", Decimal("3500")),
        ("Кроссовки женские 3500₽", "Кроссовки женские", Decimal("3500")),
        ("Кроссовки женские — 3500 руб", "Кроссовки женские", Decimal("3500")),
        ("Кроссовки женские 3 500", "Кроссовки женские", Decimal("3500")),
        ("Кроссовки женские - 3500", "Кроссовки женские", Decimal("3500")),
    ],
)
def test_parse_caption(caption: str, category: str, price: Decimal) -> None:
    assert parse_caption(caption).category == category
    assert parse_caption(caption).price_rub == price


@pytest.mark.parametrize("caption", [None, "", "Кроссовки", "3500", "Товар бесплатно"])
def test_invalid_caption(caption: str | None) -> None:
    with pytest.raises(CaptionParseError):
        parse_caption(caption)

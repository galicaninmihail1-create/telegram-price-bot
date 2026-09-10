import re
from decimal import Decimal

from app.domain.models import ParsedProduct


class CaptionParseError(ValueError):
    """Caption does not end with a valid positive RUB price."""


_PRICE_RE = re.compile(
    r"^(?P<category>.+?)\s*(?:[-–—]\s*)?"
    r"(?P<price>\d{1,3}(?:[ \u00a0]\d{3})*|\d+)\s*"
    r"(?:₽|руб(?:\.|лей)?)?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def parse_caption(caption: str | None) -> ParsedProduct:
    if not caption or not (match := _PRICE_RE.fullmatch(caption.strip())):
        raise CaptionParseError("Не удалось определить категорию и цену")
    category = match.group("category").strip().rstrip("-–— ").strip()
    if not category or not any(character.isalpha() for character in category):
        raise CaptionParseError("Не указана категория товара")
    price = Decimal(re.sub(r"[ \u00a0]", "", match.group("price")))
    if price <= 0:
        raise CaptionParseError("Цена должна быть больше нуля")
    return ParsedProduct(category=category, price_rub=price)

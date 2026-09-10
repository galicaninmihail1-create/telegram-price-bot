from decimal import Decimal


def _display_price(value: Decimal) -> str:
    formatted = format(value, "f")
    return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted


def format_post(category: str, final_price_byn: Decimal) -> str:
    return (
        f"👟 {category}\n\n"
        f"💰 Цена: {_display_price(final_price_byn)} BYN\n\n"
        "Для заказа пишите в личные сообщения."
    )

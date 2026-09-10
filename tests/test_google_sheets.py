from datetime import UTC, datetime
from decimal import Decimal

from app.domain.models import ProcessedProduct
from app.services.google_sheets import SHEET_COLUMNS, product_to_row

EXPECTED_COLUMNS = (
    "created_at",
    "telegram_message_id",
    "category",
    "price_rub",
    "rub_byn_rate",
    "base_price_byn",
    "markup_percent",
    "final_price_byn",
    "drive_file_id",
    "drive_url",
    "status",
)


def test_sheet_columns_and_append_row_have_the_same_order() -> None:
    product = ProcessedProduct(
        created_at=datetime(2026, 9, 10, 12, 0, tzinfo=UTC),
        telegram_message_id=42,
        category="Кроссовки женские",
        price_rub=Decimal("3500"),
        rub_byn_rate=Decimal("0.035698"),
        base_price_byn=Decimal("124.943"),
        markup_percent=Decimal("0"),
        final_price_byn=Decimal("125"),
        drive_file_id="file-id",
        drive_url="https://drive.invalid/file-id",
    )

    row = product_to_row(product)

    assert SHEET_COLUMNS == EXPECTED_COLUMNS
    assert len(row) == len(SHEET_COLUMNS)
    assert dict(zip(SHEET_COLUMNS, row, strict=True)) == {
        "created_at": "2026-09-10T12:00:00+00:00",
        "telegram_message_id": 42,
        "category": "Кроссовки женские",
        "price_rub": 3500.0,
        "rub_byn_rate": 0.035698,
        "base_price_byn": 124.943,
        "markup_percent": 0.0,
        "final_price_byn": 125.0,
        "drive_file_id": "file-id",
        "drive_url": "https://drive.invalid/file-id",
        "status": "SUCCESS",
    }

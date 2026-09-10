from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ParsedProduct:
    category: str
    price_rub: Decimal


@dataclass(frozen=True, slots=True)
class PriceResult:
    base_price_byn: Decimal
    final_price_byn: Decimal


@dataclass(frozen=True, slots=True)
class ProcessedProduct:
    created_at: datetime
    telegram_message_id: int | str
    category: str
    price_rub: Decimal
    rub_byn_rate: Decimal
    base_price_byn: Decimal
    markup_percent: Decimal
    final_price_byn: Decimal
    drive_file_id: str
    drive_url: str
    status: str = "SUCCESS"

import asyncio
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.models import ProcessedProduct
from app.services.currency import CurrencyService
from app.services.google_drive import GoogleDriveService
from app.services.google_sheets import GoogleSheetsService
from app.services.price_calculator import PriceCalculator
from app.utils.parsing import parse_caption


class DuplicateMessageError(RuntimeError):
    pass


def _slugify(value: str) -> str:
    letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    replacements = (
        "a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y",
        "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f",
        "h", "c", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya",
    )
    value = value.lower().translate(str.maketrans(dict(zip(letters, replacements, strict=True))))
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "product"


class ProductService:
    def __init__(
        self,
        currency: CurrencyService,
        calculator: PriceCalculator,
        drive: GoogleDriveService,
        sheets: GoogleSheetsService,
    ) -> None:
        self._currency = currency
        self._calculator = calculator
        self._drive = drive
        self._sheets = sheets
        self._processing: set[int] = set()
        self._processed: set[int] = set()
        self._lock = asyncio.Lock()

    async def process(self, message_id: int, caption: str | None, photo: bytes) -> ProcessedProduct:
        async with self._lock:
            if message_id in self._processing or message_id in self._processed:
                raise DuplicateMessageError("Это сообщение уже обработано")
            self._processing.add(message_id)
        try:
            parsed = parse_caption(caption)
            rate = await self._currency.get_rub_to_byn_rate()
            price = self._calculator.calculate(parsed.price_rub, rate)
            now = datetime.now(ZoneInfo("Europe/Minsk"))
            filename = f"{now:%Y-%m-%d_%H%M%S}_{_slugify(parsed.category)}.jpg"
            file_id, drive_url = await self._drive.upload(photo, filename)
            product = ProcessedProduct(
                created_at=now,
                telegram_message_id=message_id,
                category=parsed.category,
                price_rub=parsed.price_rub,
                rub_byn_rate=rate,
                base_price_byn=price.base_price_byn,
                markup_percent=self._calculator.markup_percent,
                final_price_byn=price.final_price_byn,
                drive_file_id=file_id,
                drive_url=drive_url,
            )
            await self._sheets.append(product)
            async with self._lock:
                self._processed.add(message_id)
            return product
        finally:
            async with self._lock:
                self._processing.discard(message_id)

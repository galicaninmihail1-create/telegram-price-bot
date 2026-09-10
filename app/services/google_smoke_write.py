import mimetypes
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from app.domain.models import ProcessedProduct
from app.services.google_drive import GoogleDriveService
from app.services.google_sheets import GoogleSheetsError, GoogleSheetsService

ALLOWED_IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}


class SmokeImageError(ValueError):
    """The smoke-test image is missing or unsupported."""


class SmokeSheetsWriteError(RuntimeError):
    """Drive upload succeeded, but the Sheets append failed."""

    def __init__(self, drive_file_id: str, drive_url: str) -> None:
        super().__init__("Google Sheets append failed; uploaded file remains in Google Drive")
        self.drive_file_id = drive_file_id
        self.drive_url = drive_url


class GoogleSmokeWriteService:
    def __init__(self, drive: GoogleDriveService, sheets: GoogleSheetsService) -> None:
        self._drive = drive
        self._sheets = sheets

    async def run(self, image_path: Path) -> ProcessedProduct:
        image_path = image_path.expanduser().resolve()
        extension = image_path.suffix.lower()
        if not image_path.is_file():
            raise SmokeImageError(f"Файл не найден: {image_path}")
        if extension not in ALLOWED_IMAGE_TYPES:
            raise SmokeImageError("Поддерживаются только JPG, JPEG и PNG")
        content = image_path.read_bytes()
        if not content:
            raise SmokeImageError("Файл изображения пуст")

        now = datetime.now(ZoneInfo("Europe/Minsk"))
        filename = f"smoke-test-{now:%Y%m%d-%H%M%S-%f}{extension}"
        mime_type = ALLOWED_IMAGE_TYPES.get(extension) or mimetypes.guess_type(image_path.name)[0]
        drive_file_id, drive_url = await self._drive.upload(content, filename, mime_type or "image/jpeg")
        product = ProcessedProduct(
            created_at=now,
            telegram_message_id="SMOKE_TEST",
            category="TEST PRODUCT",
            price_rub=Decimal("1000"),
            rub_byn_rate=Decimal("0.035"),
            base_price_byn=Decimal("35"),
            markup_percent=Decimal("0"),
            final_price_byn=Decimal("35"),
            drive_file_id=drive_file_id,
            drive_url=drive_url,
            status="TEST",
        )
        try:
            await self._sheets.append(product)
        except GoogleSheetsError as exc:
            raise SmokeSheetsWriteError(drive_file_id, drive_url) from exc
        return product

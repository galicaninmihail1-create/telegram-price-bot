import asyncio
from decimal import Decimal

from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.domain.models import ProcessedProduct
from app.services.google_common import GoogleCredentialProvider

SHEET_COLUMNS = (
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


class GoogleSheetsError(RuntimeError):
    pass


def _cell(value: Decimal) -> float:
    return float(value)


def product_to_row(product: ProcessedProduct) -> list[str | int | float]:
    return [
        product.created_at.isoformat(),
        product.telegram_message_id,
        product.category,
        _cell(product.price_rub),
        _cell(product.rub_byn_rate),
        _cell(product.base_price_byn),
        _cell(product.markup_percent),
        _cell(product.final_price_byn),
        product.drive_file_id,
        product.drive_url,
        product.status,
    ]


class GoogleSheetsService:
    def __init__(
        self,
        credential_provider: GoogleCredentialProvider,
        spreadsheet_id: str,
        worksheet: str,
    ) -> None:
        self._credential_provider = credential_provider
        self._spreadsheet_id = spreadsheet_id
        self._worksheet = worksheet

    async def append(self, product: ProcessedProduct) -> None:
        await asyncio.to_thread(self._append_sync, product)

    def _append_sync(self, product: ProcessedProduct) -> None:
        values = [product_to_row(product)]
        try:
            service = build(
                "sheets",
                "v4",
                credentials=self._credential_provider.get_credentials(),
                cache_discovery=False,
            )
            service.spreadsheets().values().append(
                spreadsheetId=self._spreadsheet_id,
                range=f"'{self._worksheet}'!A:K",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values},
            ).execute()
        except (GoogleAuthError, HttpError, OSError, ValueError) as exc:
            raise GoogleSheetsError("Не удалось записать товар в Google Sheets") from exc

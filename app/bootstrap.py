from aiogram import Dispatcher

from app.bot.handlers import router
from app.config import Settings
from app.services.currency import CurrencyService
from app.services.google_common import GoogleCredentialProvider
from app.services.google_drive import GoogleDriveService
from app.services.google_sheets import GoogleSheetsService
from app.services.price_calculator import PriceCalculator
from app.services.product_service import ProductService


def build_dispatcher(settings: Settings) -> Dispatcher:
    google_credentials = GoogleCredentialProvider(
        settings.google_oauth_client_file,
        settings.google_oauth_token_file,
    )
    product_service = ProductService(
        CurrencyService(),
        PriceCalculator(settings.markup_percent, settings.fixed_markup_byn, settings.price_rounding),
        GoogleDriveService(google_credentials, settings.google_drive_folder_id),
        GoogleSheetsService(
            google_credentials,
            settings.google_sheets_spreadsheet_id,
            settings.google_sheets_worksheet,
        ),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher["product_service"] = product_service
    dispatcher["allowed_user_id"] = settings.allowed_telegram_user_id
    return dispatcher

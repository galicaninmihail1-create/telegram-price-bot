from decimal import Decimal
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GoogleSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_oauth_client_file: Path
    google_oauth_token_file: Path
    google_drive_folder_id: str = ""
    google_sheets_spreadsheet_id: str
    google_sheets_worksheet: str = "Products"


class Settings(GoogleSettings):
    telegram_bot_token: str
    telegram_proxy_url: str = ""
    allowed_telegram_user_id: int
    markup_percent: Decimal = Decimal("0")
    fixed_markup_byn: Decimal = Decimal("0")
    price_rounding: Decimal = Decimal("1")
    log_level: str = "INFO"
    webhook_secret: str | None = Field(default=None)

    @field_validator("price_rounding")
    @classmethod
    def positive_rounding(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("PRICE_ROUNDING must be positive")
        return value

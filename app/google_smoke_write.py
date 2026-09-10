import argparse
import asyncio
from pathlib import Path

from app.config import GoogleSettings
from app.services.google_common import GoogleCredentialProvider
from app.services.google_drive import GoogleDriveError, GoogleDriveService
from app.services.google_sheets import GoogleSheetsService
from app.services.google_smoke_write import (
    GoogleSmokeWriteService,
    SmokeImageError,
    SmokeSheetsWriteError,
)


async def _run(image_path: Path) -> None:
    settings = GoogleSettings()  # type: ignore[call-arg]
    credentials = GoogleCredentialProvider(
        settings.google_oauth_client_file,
        settings.google_oauth_token_file,
    )
    drive = GoogleDriveService(credentials, settings.google_drive_folder_id)
    sheets = GoogleSheetsService(
        credentials,
        settings.google_sheets_spreadsheet_id,
        settings.google_sheets_worksheet,
    )
    product = await GoogleSmokeWriteService(drive, sheets).run(image_path)
    print("Google Drive upload: OK")
    print("Google Sheets append: OK")
    print(f"Category: {product.category}")
    print(f"Final price: {product.final_price_byn} BYN")


def main() -> None:
    parser = argparse.ArgumentParser(description="One controlled Google Drive/Sheets write smoke-test")
    parser.add_argument("image", type=Path, help="Path to a local JPG or PNG")
    args = parser.parse_args()
    try:
        asyncio.run(_run(args.image))
    except SmokeSheetsWriteError as exc:
        raise SystemExit(
            "Google Drive upload: OK\n"
            "Google Sheets append: FAILED\n"
            "The uploaded file remains in Google Drive.\n"
            f"Drive file ID: {exc.drive_file_id}\n"
            f"Drive URL: {exc.drive_url}"
        ) from exc
    except (GoogleDriveError, SmokeImageError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

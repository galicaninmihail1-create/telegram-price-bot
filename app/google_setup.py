from app.config import GoogleSettings
from app.services.google_common import GoogleCredentialProvider
from app.services.google_setup import GoogleSetupError, build_google_setup_service


def main() -> None:
    settings = GoogleSettings()  # type: ignore[call-arg]
    provider = GoogleCredentialProvider(
        settings.google_oauth_client_file,
        settings.google_oauth_token_file,
    )
    try:
        result = build_google_setup_service(provider).setup(
            settings.google_drive_folder_id,
            settings.google_sheets_spreadsheet_id,
            settings.google_sheets_worksheet,
        )
    except GoogleSetupError as exc:
        raise SystemExit(str(exc)) from exc

    action = "создана" if result.folder_created else "найдена и проверена"
    print(f"Папка {action}. GOOGLE_DRIVE_FOLDER_ID={result.folder_id}")
    if result.folder_created:
        print("Скопируйте этот ID в .env вручную; файл .env не изменялся.")
    print(f"Таблица и лист {result.worksheet!r} доступны для чтения.")


if __name__ == "__main__":
    main()

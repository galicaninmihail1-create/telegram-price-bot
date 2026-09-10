from dataclasses import dataclass
from typing import Any

from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.google_common import GoogleCredentialProvider

FOLDER_NAME = "Telegram Price Bot Photos"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


class GoogleSetupError(RuntimeError):
    """Google Drive or Sheets setup validation failed."""


@dataclass(frozen=True, slots=True)
class GoogleSetupResult:
    folder_id: str
    folder_created: bool
    spreadsheet_title: str
    worksheet: str


class GoogleSetupService:
    def __init__(self, drive: Any, sheets: Any) -> None:
        self._drive = drive
        self._sheets = sheets

    def setup(self, folder_id: str, spreadsheet_id: str, worksheet: str) -> GoogleSetupResult:
        if not spreadsheet_id.strip():
            raise GoogleSetupError("GOOGLE_SHEETS_SPREADSHEET_ID не задан")
        if not worksheet.strip():
            raise GoogleSetupError("GOOGLE_SHEETS_WORKSHEET не задан")
        try:
            resolved_folder_id, folder_created = self._resolve_folder(folder_id.strip())
            spreadsheet = self._sheets.spreadsheets().get(
                spreadsheetId=spreadsheet_id.strip(),
                fields="properties.title,sheets.properties(title,sheetId)",
            ).execute()
            titles = {
                item["properties"]["title"]
                for item in spreadsheet.get("sheets", [])
                if "properties" in item and "title" in item["properties"]
            }
            if worksheet not in titles:
                raise GoogleSetupError(f"Лист {worksheet!r} не найден в таблице")
            return GoogleSetupResult(
                folder_id=resolved_folder_id,
                folder_created=folder_created,
                spreadsheet_title=spreadsheet.get("properties", {}).get("title", ""),
                worksheet=worksheet,
            )
        except GoogleSetupError:
            raise
        except (GoogleAuthError, HttpError, KeyError, OSError, TypeError, ValueError) as exc:
            raise GoogleSetupError("Не удалось проверить Google Drive/Sheets") from exc

    def _resolve_folder(self, folder_id: str) -> tuple[str, bool]:
        files = self._drive.files()
        if folder_id:
            folder = files.get(
                fileId=folder_id,
                fields="id,name,mimeType,trashed",
                supportsAllDrives=True,
            ).execute()
            if folder.get("mimeType") != FOLDER_MIME_TYPE or folder.get("trashed"):
                raise GoogleSetupError("GOOGLE_DRIVE_FOLDER_ID не указывает на доступную папку")
            return folder["id"], False

        result = files.list(
            q=f"name = '{FOLDER_NAME}' and mimeType = '{FOLDER_MIME_TYPE}' and trashed = false",
            spaces="drive",
            fields="files(id,name)",
            pageSize=10,
        ).execute()
        existing = result.get("files", [])
        if existing:
            return existing[0]["id"], False
        folder = files.create(
            body={"name": FOLDER_NAME, "mimeType": FOLDER_MIME_TYPE},
            fields="id",
        ).execute()
        return folder["id"], True


def build_google_setup_service(provider: GoogleCredentialProvider) -> GoogleSetupService:
    credentials = provider.get_credentials()
    drive = build("drive", "v3", credentials=credentials, cache_discovery=False)
    sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    return GoogleSetupService(drive, sheets)

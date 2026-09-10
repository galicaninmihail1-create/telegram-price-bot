from unittest.mock import MagicMock

import pytest

from app.services.google_setup import FOLDER_MIME_TYPE, GoogleSetupError, GoogleSetupService


def _services() -> tuple[MagicMock, MagicMock, GoogleSetupService]:
    drive = MagicMock()
    sheets = MagicMock()
    sheets.spreadsheets().get().execute.return_value = {
        "properties": {"title": "Catalog"},
        "sheets": [{"properties": {"title": "Products", "sheetId": 1}}],
    }
    return drive, sheets, GoogleSetupService(drive, sheets)


def test_creates_folder_when_id_and_existing_app_folder_are_missing() -> None:
    drive, sheets, service = _services()
    drive.files().list().execute.return_value = {"files": []}
    drive.files.return_value.create.return_value.execute.return_value = {"id": "new-folder-id"}

    result = service.setup("", "spreadsheet-id", "Products")

    assert result.folder_id == "new-folder-id"
    assert result.folder_created is True
    drive.files().create.assert_called_once_with(
        body={"name": "Telegram Price Bot Photos", "mimeType": FOLDER_MIME_TYPE},
        fields="id",
    )
    sheets.spreadsheets().values().append.assert_not_called()


def test_reuses_app_created_folder_instead_of_creating_duplicate() -> None:
    drive, _, service = _services()
    drive.files().list().execute.return_value = {
        "files": [{"id": "existing-folder-id", "name": "Telegram Price Bot Photos"}]
    }

    result = service.setup("", "spreadsheet-id", "Products")

    assert result.folder_id == "existing-folder-id"
    assert result.folder_created is False
    drive.files().create.assert_not_called()


def test_checks_configured_folder_and_worksheet_without_writes() -> None:
    drive, sheets, service = _services()
    drive.files().get().execute.return_value = {
        "id": "configured-folder-id",
        "mimeType": FOLDER_MIME_TYPE,
        "trashed": False,
    }

    result = service.setup("configured-folder-id", "spreadsheet-id", "Products")

    assert result.folder_id == "configured-folder-id"
    drive.files().list.assert_not_called()
    drive.files().create.assert_not_called()
    sheets.spreadsheets().values().append.assert_not_called()


def test_rejects_missing_spreadsheet_before_drive_calls() -> None:
    drive, _, service = _services()

    with pytest.raises(GoogleSetupError, match="GOOGLE_SHEETS_SPREADSHEET_ID"):
        service.setup("", "", "Products")

    drive.files.assert_not_called()


def test_rejects_missing_worksheet() -> None:
    drive, _, service = _services()
    drive.files().get().execute.return_value = {
        "id": "folder-id",
        "mimeType": FOLDER_MIME_TYPE,
        "trashed": False,
    }

    with pytest.raises(GoogleSetupError, match="не найден"):
        service.setup("folder-id", "spreadsheet-id", "Missing")

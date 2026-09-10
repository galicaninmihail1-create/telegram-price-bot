import asyncio
import io

from google.auth.exceptions import GoogleAuthError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from app.services.google_common import GoogleCredentialProvider


class GoogleDriveError(RuntimeError):
    pass


class GoogleDriveService:
    def __init__(self, credential_provider: GoogleCredentialProvider, folder_id: str) -> None:
        self._credential_provider = credential_provider
        self._folder_id = folder_id

    async def upload(self, content: bytes, filename: str, mime_type: str = "image/jpeg") -> tuple[str, str]:
        return await asyncio.to_thread(self._upload_sync, content, filename, mime_type)

    def _upload_sync(self, content: bytes, filename: str, mime_type: str) -> tuple[str, str]:
        try:
            service = build(
                "drive",
                "v3",
                credentials=self._credential_provider.get_credentials(),
                cache_discovery=False,
            )
            media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
            result = service.files().create(
                body={"name": filename, "parents": [self._folder_id]},
                media_body=media,
                fields="id,webViewLink",
                supportsAllDrives=True,
            ).execute()
            return result["id"], result.get("webViewLink", f"https://drive.google.com/file/d/{result['id']}/view")
        except (GoogleAuthError, HttpError, OSError, KeyError, ValueError) as exc:
            raise GoogleDriveError("Не удалось загрузить фото в Google Drive") from exc

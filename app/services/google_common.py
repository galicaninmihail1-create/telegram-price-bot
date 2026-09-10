import threading
from pathlib import Path

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = (
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
)


class GoogleCredentialsError(RuntimeError):
    """OAuth credentials could not be loaded, refreshed, or created."""


class GoogleCredentialProvider:
    """Lazily creates and shares one OAuth credential set across Google services."""

    def __init__(self, client_file: Path, token_file: Path) -> None:
        self._client_file = client_file
        self._token_file = token_file
        self._credentials: Credentials | None = None
        self._lock = threading.Lock()

    def get_credentials(self) -> Credentials:
        with self._lock:
            if self._credentials and self._credentials.valid:
                return self._credentials
            try:
                credentials = self._credentials or self._load_token()
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    self._save_token(credentials)
                elif not credentials or not credentials.valid:
                    credentials = self._run_desktop_flow()
                    self._save_token(credentials)
            except (GoogleAuthError, OSError, ValueError) as exc:
                raise GoogleCredentialsError("Не удалось выполнить авторизацию Google OAuth") from exc
            self._credentials = credentials
            return credentials

    def _load_token(self) -> Credentials | None:
        if not self._token_file.is_file():
            return None
        return Credentials.from_authorized_user_file(str(self._token_file), scopes=SCOPES)

    def _run_desktop_flow(self) -> Credentials:
        flow = InstalledAppFlow.from_client_secrets_file(str(self._client_file), scopes=SCOPES)
        return flow.run_local_server(port=0, open_browser=True)

    def _save_token(self, credentials: Credentials) -> None:
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self._token_file.with_suffix(self._token_file.suffix + ".tmp")
        temporary_file.write_text(credentials.to_json(), encoding="utf-8")
        temporary_file.replace(self._token_file)

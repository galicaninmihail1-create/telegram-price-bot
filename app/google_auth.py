from app.config import GoogleSettings
from app.services.google_common import GoogleCredentialProvider


def main() -> None:
    settings = GoogleSettings()  # type: ignore[call-arg]
    provider = GoogleCredentialProvider(
        settings.google_oauth_client_file,
        settings.google_oauth_token_file,
    )
    provider.get_credentials()
    print("Google OAuth авторизация успешно сохранена.")


if __name__ == "__main__":
    main()

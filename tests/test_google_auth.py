from unittest.mock import Mock, patch

from app.services.google_common import SCOPES, GoogleCredentialProvider


def test_reuses_valid_token_and_shared_credentials(tmp_path) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("not-a-real-token", encoding="utf-8")
    credentials = Mock(valid=True, expired=False, refresh_token=None)
    provider = GoogleCredentialProvider(tmp_path / "client.json", token_file)

    with patch(
        "app.services.google_common.Credentials.from_authorized_user_file",
        return_value=credentials,
    ) as load_token:
        assert provider.get_credentials() is credentials
        assert provider.get_credentials() is credentials

    load_token.assert_called_once_with(str(token_file), scopes=SCOPES)


def test_refreshes_expired_token_without_login(tmp_path) -> None:
    token_file = tmp_path / "token.json"
    token_file.write_text("not-a-real-token", encoding="utf-8")
    credentials = Mock(valid=False, expired=True, refresh_token="refresh-token")
    credentials.to_json.return_value = '{"safe": "fake"}'

    def refresh(_request) -> None:
        credentials.valid = True

    credentials.refresh.side_effect = refresh
    provider = GoogleCredentialProvider(tmp_path / "client.json", token_file)

    with (
        patch(
            "app.services.google_common.Credentials.from_authorized_user_file",
            return_value=credentials,
        ),
        patch("app.services.google_common.InstalledAppFlow") as desktop_flow,
    ):
        assert provider.get_credentials() is credentials

    credentials.refresh.assert_called_once()
    desktop_flow.from_client_secrets_file.assert_not_called()
    assert token_file.read_text(encoding="utf-8") == '{"safe": "fake"}'


def test_first_login_uses_desktop_flow_and_saves_token(tmp_path) -> None:
    client_file = tmp_path / "client.json"
    token_file = tmp_path / "token.json"
    credentials = Mock(valid=True)
    credentials.to_json.return_value = '{"safe": "fake"}'
    flow = Mock()
    flow.run_local_server.return_value = credentials
    provider = GoogleCredentialProvider(client_file, token_file)

    with patch(
        "app.services.google_common.InstalledAppFlow.from_client_secrets_file",
        return_value=flow,
    ) as create_flow:
        assert provider.get_credentials() is credentials

    create_flow.assert_called_once_with(str(client_file), scopes=SCOPES)
    flow.run_local_server.assert_called_once_with(port=0, open_browser=True)
    assert token_file.read_text(encoding="utf-8") == '{"safe": "fake"}'

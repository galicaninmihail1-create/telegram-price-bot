from unittest.mock import Mock, patch

import pytest

from app.bot.factory import create_telegram_session


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("http://127.0.0.1:10809", "http://127.0.0.1:10809"),
        ("  http://127.0.0.1:10809  ", "http://127.0.0.1:10809"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_session_receives_configured_proxy(configured: str | None, expected: str | None) -> None:
    session = Mock()
    with patch("app.bot.factory.AiohttpSession", return_value=session) as session_class:
        assert create_telegram_session(configured) is session

    session_class.assert_called_once_with(proxy=expected)

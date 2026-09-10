from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.handlers import (
    ACCESS_DENIED,
    FORMAT_HELP,
    WELCOME_TEXT,
    help_command,
    photo,
    start,
    unsupported,
)
from app.utils.parsing import CaptionParseError


def _message(user_id: int, *, caption: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        from_user=SimpleNamespace(id=user_id),
        answer=AsyncMock(),
        answer_photo=AsyncMock(),
        caption=caption,
        message_id=42,
        photo=[SimpleNamespace(file_id="offline-photo-id")],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [start, help_command])
async def test_start_and_help_for_allowed_user(handler) -> None:
    message = _message(100)

    await handler(message, allowed_user_id=100)

    message.answer.assert_awaited_once_with(WELCOME_TEXT)


@pytest.mark.asyncio
async def test_text_without_photo_shows_format_help() -> None:
    message = _message(100)

    await unsupported(message, allowed_user_id=100)

    message.answer.assert_awaited_once_with(FORMAT_HELP)


@pytest.mark.asyncio
async def test_photo_without_caption_stops_before_external_calls() -> None:
    message = _message(100)
    bot = SimpleNamespace(download=AsyncMock())
    product_service = SimpleNamespace(process=AsyncMock())

    await photo(message, bot, product_service, allowed_user_id=100)

    message.answer.assert_awaited_once_with(FORMAT_HELP)
    bot.download.assert_not_awaited()
    product_service.process.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_price_shows_format_help() -> None:
    message = _message(100, caption="Кроссовки бесплатно")
    bot = SimpleNamespace(download=AsyncMock())
    product_service = SimpleNamespace(process=AsyncMock(side_effect=CaptionParseError()))

    await photo(message, bot, product_service, allowed_user_id=100)

    message.answer.assert_awaited_once_with(FORMAT_HELP)
    product_service.process.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("handler", [start, help_command, unsupported])
async def test_unauthorized_simple_handlers(handler) -> None:
    message = _message(999)

    await handler(message, allowed_user_id=100)

    message.answer.assert_awaited_once_with(ACCESS_DENIED)


@pytest.mark.asyncio
async def test_unauthorized_photo_never_calls_external_services() -> None:
    message = _message(999, caption="Кроссовки 3500")
    bot = SimpleNamespace(download=AsyncMock())
    product_service = SimpleNamespace(process=AsyncMock())

    await photo(message, bot, product_service, allowed_user_id=100)

    message.answer.assert_awaited_once_with(ACCESS_DENIED)
    bot.download.assert_not_awaited()
    product_service.process.assert_not_awaited()

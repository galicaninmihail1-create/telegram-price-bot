from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from app.config import Settings


def create_telegram_session(proxy_url: str | None) -> AiohttpSession:
    normalized_proxy = proxy_url.strip() if proxy_url else None
    return AiohttpSession(proxy=normalized_proxy or None)


def create_bot(settings: Settings) -> Bot:
    session = create_telegram_session(settings.telegram_proxy_url)
    return Bot(settings.telegram_bot_token, session=session)

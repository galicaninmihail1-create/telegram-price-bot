import asyncio
import json
import logging
from collections.abc import Callable, Iterable
from functools import lru_cache
from http import HTTPStatus

from aiogram import Dispatcher
from aiogram.types import Update

from app.bootstrap import build_dispatcher
from app.bot.factory import create_bot
from app.config import Settings


@lru_cache(maxsize=1)
def _runtime() -> tuple[Settings, Dispatcher]:
    settings = Settings()  # type: ignore[call-arg]
    logging.basicConfig(level=settings.log_level)
    return settings, build_dispatcher(settings)


def application(environ: dict, start_response: Callable) -> Iterable[bytes]:
    settings, dispatcher = _runtime()
    secret = environ.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN")
    if (
        environ.get("REQUEST_METHOD") != "POST"
        or not settings.webhook_secret
        or secret != settings.webhook_secret
    ):
        start_response(f"{HTTPStatus.FORBIDDEN.value} Forbidden", [("Content-Type", "text/plain")])
        return [b"Forbidden"]
    try:
        length = int(environ.get("CONTENT_LENGTH", "0"))
        payload = json.loads(environ["wsgi.input"].read(length))

        async def feed() -> None:
            bot = create_bot(settings)
            try:
                await dispatcher.feed_update(bot, Update.model_validate(payload))
            finally:
                await bot.session.close()

        asyncio.run(feed())
    except Exception:
        logging.exception("Webhook update failed")
        start_response(f"{HTTPStatus.BAD_REQUEST.value} Bad Request", [("Content-Type", "text/plain")])
        return [b"Bad Request"]
    start_response(f"{HTTPStatus.OK.value} OK", [("Content-Type", "text/plain")])
    return [b"OK"]

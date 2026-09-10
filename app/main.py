import asyncio
import logging

from app.bootstrap import build_dispatcher
from app.bot.factory import create_bot
from app.config import Settings


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    bot = create_bot(settings)
    try:
        await build_dispatcher(settings).start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from decimal import Decimal

from app.bot.factory import create_bot
from app.config import Settings
from app.services.currency import CurrencyService, CurrencyServiceError


def _decimal(value: Decimal) -> str:
    return format(value, "f")


async def _check_telegram(settings: Settings) -> bool:
    bot = create_bot(settings)
    try:
        await bot.get_me()
    except Exception as exc:
        print(f"Telegram API: ERROR ({type(exc).__name__})")
        return False
    finally:
        await bot.session.close()
    print("Telegram API: OK")
    return True


async def _check_nbrb() -> bool:
    try:
        rate = await CurrencyService().get_rub_rate()
    except CurrencyServiceError as exc:
        print(f"NBRB API: ERROR ({type(exc.__cause__).__name__})")
        return False
    print("NBRB API: OK")
    print(f"RUB scale: {_decimal(rate.scale)}")
    print(f"RUB official rate: {_decimal(rate.official_rate)}")
    print(f"RUB/BYN per 1 RUB: {_decimal(rate.per_one_rub)}")
    return True


async def _run() -> int:
    settings = Settings()  # type: ignore[call-arg]
    telegram_ok, nbrb_ok = await asyncio.gather(_check_telegram(settings), _check_nbrb())
    return 0 if telegram_ok and nbrb_ok else 1


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()

import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.formatting import format_post
from app.services.currency import CurrencyServiceError
from app.services.google_drive import GoogleDriveError
from app.services.google_sheets import GoogleSheetsError
from app.services.product_service import DuplicateMessageError, ProductService
from app.utils.parsing import CaptionParseError

logger = logging.getLogger(__name__)
router = Router()
ACCESS_DENIED = "Нет доступа"
FORMAT_HELP = (
    "Не удалось определить цену. Отправьте фото с подписью, например:\n"
    "Кроссовки женские 3500"
)
WELCOME_TEXT = (
    "👋 Бот готов к работе.\n\n"
    "Отправьте фотографию товара с подписью:\n"
    "Кроссовки женские 3500\n\n"
    "Я:\n"
    "• определю название и цену;\n"
    "• получу актуальный курс RUB/BYN;\n"
    "• рассчитаю цену;\n"
    "• сохраню фото в Google Drive;\n"
    "• добавлю данные в Google Sheets;\n"
    "• верну готовый пост."
)
GOOGLE_ERROR = "Не удалось сохранить данные. Попробуйте позже."


def _allowed(message: Message, allowed_user_id: int) -> bool:
    return message.from_user is not None and message.from_user.id == allowed_user_id


@router.message(CommandStart())
async def start(message: Message, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer(ACCESS_DENIED)
        return
    await message.answer(WELCOME_TEXT)


@router.message(Command("help"))
async def help_command(message: Message, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer(ACCESS_DENIED)
        return
    await message.answer(WELCOME_TEXT)


@router.message(F.photo)
async def photo(message: Message, bot: Bot, product_service: ProductService, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer(ACCESS_DENIED)
        return
    if not message.caption:
        await message.answer(FORMAT_HELP)
        return
    try:
        buffer = io.BytesIO()
        await bot.download(message.photo[-1], destination=buffer)
        result = await product_service.process(message.message_id, message.caption, buffer.getvalue())
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=format_post(result.category, result.final_price_byn),
        )
    except CaptionParseError:
        await message.answer(FORMAT_HELP)
    except DuplicateMessageError as exc:
        await message.answer(str(exc))
    except CurrencyServiceError:
        logger.exception("NBRB exchange rate request failed for message_id=%s", message.message_id)
        await message.answer("Не удалось получить актуальный курс. Попробуйте позже.")
    except GoogleDriveError:
        logger.exception("Google Drive upload failed for message_id=%s", message.message_id)
        await message.answer(GOOGLE_ERROR)
    except GoogleSheetsError:
        logger.exception("Google Sheets append failed for message_id=%s", message.message_id)
        await message.answer(GOOGLE_ERROR)
    except Exception:
        logger.exception(
            "Telegram download or unexpected processing error, message_id=%s",
            message.message_id,
        )
        await message.answer("Не удалось обработать фотографию. Попробуйте позже.")


@router.message()
async def unsupported(message: Message, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer(ACCESS_DENIED)
        return
    await message.answer(FORMAT_HELP)

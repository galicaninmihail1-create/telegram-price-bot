import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.formatting import format_post
from app.services.currency import CurrencyServiceError
from app.services.google_drive import GoogleDriveError
from app.services.google_sheets import GoogleSheetsError
from app.services.product_service import DuplicateMessageError, ProductService
from app.utils.parsing import CaptionParseError

logger = logging.getLogger(__name__)
router = Router()
FORMAT_HELP = (
    "Не удалось определить цену. Отправьте фото с подписью, например:\n"
    "Кроссовки женские 3500"
)


def _allowed(message: Message, allowed_user_id: int) -> bool:
    return message.from_user is not None and message.from_user.id == allowed_user_id


@router.message(CommandStart())
async def start(message: Message, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer("Нет доступа")
        return
    await message.answer("Отправьте фотографию товара с категорией и ценой в RUB в подписи.")


@router.message(F.photo)
async def photo(message: Message, bot: Bot, product_service: ProductService, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer("Нет доступа")
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
        await message.answer("Не удалось сохранить фотографию. Попробуйте позже.")
    except GoogleSheetsError:
        logger.exception("Google Sheets append failed for message_id=%s", message.message_id)
        await message.answer("Фотография загружена, но не удалось записать товар в таблицу.")
    except Exception:
        logger.exception(
            "Telegram download or unexpected processing error, message_id=%s",
            message.message_id,
        )
        await message.answer("Не удалось обработать фотографию. Попробуйте позже.")


@router.message()
async def unsupported(message: Message, allowed_user_id: int) -> None:
    if not _allowed(message, allowed_user_id):
        await message.answer("Нет доступа")
        return
    await message.answer(FORMAT_HELP)

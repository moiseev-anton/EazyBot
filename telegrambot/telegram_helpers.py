import asyncio
import logging
from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.types import Message


logger = logging.getLogger(__name__)


def is_message_not_modified(error: TelegramBadRequest) -> bool:
    return "message is not modified" in str(error).lower()


async def edit_message_with_retry(message: Message, **kwargs: Any) -> bool:
    """Редактирует сообщение и один раз повторяет запрос после сетевого таймаута.

    При таймауте первый запрос мог дойти до Telegram, хотя ответ не вернулся.
    Поэтому ответ ``message is not modified`` при повторной попытке считается успехом.
    """
    try:
        await message.edit_text(**kwargs)
        return True
    except TelegramBadRequest as error:
        if is_message_not_modified(error):
            return False
        raise
    except TelegramNetworkError:
        logger.warning("Telegram edit request timed out; retrying once")

    await asyncio.sleep(0.5)
    try:
        await message.edit_text(**kwargs)
        return True
    except TelegramBadRequest as error:
        if is_message_not_modified(error):
            return False
        raise

import logging

from aiogram import types
from aiogram.fsm.context import FSMContext

from managers.keyboard_manager import KeyboardManager
from managers.message_manager import MessageManager

logger = logging.getLogger(__name__)


async def handle_error(callback: types.CallbackQuery, state: FSMContext, message: str = None):
    """
    Универсальная функция для обработки ошибок.
    Отправляет стандартное сообщение об ошибке и сбрасывает состояние.
    """
    error_text = MessageManager.ERROR_DEFAULT()
    text = message if message else error_text

    await callback.message.edit_text(
        text,
        reply_markup=KeyboardManager.home
    )
    await callback.answer()

    logger.warning(f"Error handled: {text}")

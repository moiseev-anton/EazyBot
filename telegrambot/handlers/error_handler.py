import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent

from exceptions import StateExpiredError
from handlers.main_handler import main_handler
from managers import KeyboardManager, MessageManager

logger = logging.getLogger(__name__)
router = Router()


@router.error(StateExpiredError)
async def state_expired_error(event: ErrorEvent, state: FSMContext):
    """
    Функция для обработки ошибок в данных состояния.
    """
    # 1. Извлекаем callback (или message) из event.update
    update = event.update
    callback: CallbackQuery = update.callback_query

    # 3. Реакция для пользователя
    await callback.answer(
        "😅 Упс, кажется, данные устарели. Давайте начнём сначала!",
        show_alert=True,
    )
    # Переводим на главную
    await main_handler(callback, state)


@router.error()
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

import logging

from aiogram import F, Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message

from exceptions import StateExpiredError
from handlers.main_handler import main_handler
from managers import KeyboardManager, MessageManager

logger = logging.getLogger(__name__)
router = Router()


@router.error(ExceptionTypeFilter(StateExpiredError), F.update.callback_query.as_("callback"))
async def state_expired_callback_handler(event: ErrorEvent, callback: CallbackQuery, state: FSMContext):
    """ Обработка StateExpiredError в callback'ах. """
    logger.warning(f"State expired in callback from user {callback.from_user.id}: {event.exception}")
    await callback.answer(
        text=MessageManager.STATE_DATA_EXPIRED,
        show_alert=True,  # Показывает как popup
    )
    await main_handler(callback, state)


@router.error(ExceptionTypeFilter(StateExpiredError), F.update.message.as_("message"))
async def state_expired_message_handler(event: ErrorEvent, message: Message, state: FSMContext):
    """ Обработка StateExpiredError в сообщениях. """
    logger.warning(f"State expired in message from user {message.from_user.id}: {event.exception}")
    await message.answer(
        text=MessageManager.STATE_DATA_EXPIRED,
        reply_markup=KeyboardManager.home
    )
    await state.clear()


@router.error(ExceptionTypeFilter(Exception), F.update.callback_query.as_("callback"))
async def general_error_callback_handler(event: ErrorEvent, callback: CallbackQuery, state: FSMContext):
    """ Обработка любых неожиданных ошибок в обработчиках callback'ов. """
    logger.error(
        f"Unexpected error in callback from user {callback.from_user.id}: {event.exception}",
        exc_info=True  # Полный traceback в лог
    )
    await callback.message.answer(
        text=MessageManager.ERROR_DEFAULT,
        reply_markup=KeyboardManager.home  # Твоя клавиатура с кнопкой домой
    )
    await state.clear()
    await callback.answer()


@router.error(ExceptionTypeFilter(Exception), F.update.message.as_("message"))
async def general_error_message_handler(event: ErrorEvent, message: Message, state: FSMContext):
    """ Обработка любых неожиданных ошибок в хендлерах сообщений. """
    logger.error(
        f"Unexpected error in message from user {message.from_user.id}: {event.exception}",
        exc_info=True
    )
    await state.clear()
    await message.answer(
        text=MessageManager.ERROR_DEFAULT,
        reply_markup=KeyboardManager.home
    )

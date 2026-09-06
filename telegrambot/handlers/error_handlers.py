import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message

from exceptions import StateExpiredError
from handlers.main_handler import main_callback_handler
from messages import ERROR_DEFAULT, STATE_DATA_EXPIRED
from keyboards import HOME_KB
from telegram_helpers import is_message_not_modified

logger = logging.getLogger(__name__)
router = Router()


async def _answer_callback_safely(callback: CallbackQuery, **kwargs) -> None:
    try:
        await callback.answer(**kwargs)
    except TelegramBadRequest as error:
        if "query is too old" not in str(error).lower():
            raise
        logger.info("Callback query %s has already expired", callback.id)
    except TelegramNetworkError:
        logger.warning("Could not answer callback query %s due to a network error", callback.id)


@router.error(ExceptionTypeFilter(StateExpiredError), F.update.callback_query.as_("callback"))
async def state_expired_callback_handler(event: ErrorEvent, callback: CallbackQuery, state: FSMContext):
    """ Обработка StateExpiredError в callback'ах. """
    logger.warning(f"State expired in callback from user {callback.from_user.id}: {event.exception}")
    await _answer_callback_safely(
        callback,
        text=STATE_DATA_EXPIRED,
        show_alert=True,  # Показывает как popup
    )
    await main_callback_handler(callback, state)


@router.error(ExceptionTypeFilter(StateExpiredError), F.update.message.as_("message"))
async def state_expired_message_handler(event: ErrorEvent, message: Message, state: FSMContext):
    """ Обработка StateExpiredError в сообщениях. """
    logger.warning(f"State expired in message from user {message.from_user.id}: {event.exception}")
    await message.answer(
        text=STATE_DATA_EXPIRED,
        reply_markup=HOME_KB
    )
    await state.clear()


@router.error(ExceptionTypeFilter(Exception), F.update.callback_query.as_("callback"))
async def general_error_callback_handler(event: ErrorEvent, callback: CallbackQuery, state: FSMContext):
    """ Обработка любых неожиданных ошибок в обработчиках callback'ов. """
    if (
        isinstance(event.exception, TelegramBadRequest)
        and is_message_not_modified(event.exception)
    ):
        await _answer_callback_safely(callback)
        return

    if isinstance(event.exception, TelegramNetworkError):
        logger.warning(
            "Telegram request failed for callback from user %s: %s",
            callback.from_user.id,
            event.exception,
        )
        await state.clear()
        await _answer_callback_safely(callback)
        return

    logger.error(
        f"Unexpected error in callback from user {callback.from_user.id}: {event.exception}",
        exc_info=True  # traceback в лог
    )
    try:
        await callback.message.answer(
            text=ERROR_DEFAULT,
            reply_markup=HOME_KB
        )
    except TelegramNetworkError:
        logger.warning("Could not send an error message to user %s", callback.from_user.id)
    await state.clear()
    await _answer_callback_safely(callback)


@router.error(ExceptionTypeFilter(Exception), F.update.message.as_("message"))
async def general_error_message_handler(event: ErrorEvent, message: Message, state: FSMContext):
    """ Обработка любых неожиданных ошибок в хендлерах сообщений. """
    logger.error(
        f"Unexpected error in message from user {message.from_user.id}: {event.exception}",
        exc_info=True
    )
    await state.clear()
    await message.answer(
        text=ERROR_DEFAULT,
        reply_markup=HOME_KB
    )

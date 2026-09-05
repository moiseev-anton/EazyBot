import logging

from aiogram import Router, types
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from dependencies import Deps
from dto import AuthDTO
from enums import ScheduleStyle
from messages import add_rich_keyboard, get_rich_start_message, get_start_message
from services import TelegramUiPreferences, UserService
from keyboards import HOME_KB

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
@router.message(CommandStart(deep_link=True))
@inject
async def start_handler(
        message: types.Message,
        command: CommandObject,
        state: FSMContext,
        user_service: UserService = Provide[Deps.services.user],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    await state.clear()
    # Собираем данные пользователя из Telegram
    tlg_user = message.from_user
    chat_id = message.chat.id
    auth_dto = AuthDTO.from_telegram(tlg_user, chat_id)
    auth_dto.nonce = command.args

    try:
        account = await user_service.auth_user(auth_dto)

        text = get_start_message(account.user, account.created, account.nonce_status)
        schedule_style = await telegram_ui_preferences.get_schedule_style(message.from_user.id)
        reply_markup = None if auth_dto.nonce else HOME_KB
        if schedule_style == ScheduleStyle.RICH:
            rich_message = get_rich_start_message(text)
            if reply_markup:
                add_rich_keyboard(rich_message, reply_markup)
            await message.answer_rich(rich_message)
        else:
            await message.answer(text=text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error processing /start", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")

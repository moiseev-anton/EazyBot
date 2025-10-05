import logging
import traceback

from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from dto import TelegramUserDTO
from managers import KeyboardManager, MessageManager
from services import UserService

logger = logging.getLogger(__name__)
router = Router()


def map_telegram_user(user: types.User) -> TelegramUserDTO:
    return TelegramUserDTO(
        telegram_id=user.id,
        first_name=user.first_name or "",
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
        is_premium=user.is_premium or False,
        added_to_attachment_menu=user.added_to_attachment_menu or False,
    )


@router.message(CommandStart())
@router.message(CommandStart(deep_link=True))
@inject
async def start_handler(
    message: types.Message,
    command: CommandObject,
    state: FSMContext,
    user_service: UserService = Provide[Deps.services.user]
):
    await state.clear()
    # Собираем данные пользователя из Telegram
    telegram_user_dto = map_telegram_user(message.from_user)
    nonce = command.args

    try:
        user_dto = await user_service.register_user(telegram_user_dto, nonce)

        await message.answer(
            text=MessageManager.get_start_message(user_dto),
            reply_markup=KeyboardManager.home
        )
    except Exception as e:
        logger.error(f"Error processing /start", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")

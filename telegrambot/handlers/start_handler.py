import logging

from aiogram import Router, types
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from dependencies import Deps
from dto import AuthDTO
from managers import KeyboardManager, MessageManager
from services import UserService

logger = logging.getLogger(__name__)
router = Router()


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
    tlg_user = message.from_user
    auth_dto = AuthDTO.from_telegram(tlg_user)
    auth_dto.nonce = command.args

    try:
        account = await user_service.auth_user(auth_dto)

        await message.answer(
            text=MessageManager.get_start_message(account.user, account.created, account.nonce_status),
            reply_markup=KeyboardManager.home
        )
    except Exception as e:
        logger.error(f"Error processing /start", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")

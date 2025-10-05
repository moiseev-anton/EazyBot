from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from managers import MessageManager, KeyboardManager
from services import UserService

router = Router()


@router.callback_query(F.data == "main")
@inject
async def main_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        user_service: UserService = Provide[Deps.services.user],
):
    user = await user_service.get_user_with_subscriptions()

    await callback.message.edit_text(
        text=MessageManager.get_main_message(user),
        reply_markup=KeyboardManager.get_main_keyboard(user),
    )

    await state.clear()
    await callback.answer()

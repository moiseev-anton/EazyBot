from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import NavigationAction
from managers import KeyboardManager, MessageManager
from services import UserService

router = Router()


@router.callback_query(F.data == NavigationAction.MAIN)
@inject
async def main_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        user_service: UserService = Provide[Deps.services.user],
):
    user = await user_service.get_user_with_subscriptions()
    sub_id = endpoint = None
    if user.subscriptions:
        first_subscription = user.subscriptions[0]
        sub_id = first_subscription.id
        endpoint = first_subscription.link

    await callback.message.edit_text(
        text=MessageManager.get_main_message(user),
        reply_markup=KeyboardManager.get_main_keyboard(sub_id, endpoint),
    )

    await state.clear()
    await callback.answer()

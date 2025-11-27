from aiogram import F, Router, types
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import NavigationAction, ToggleEnum
from messages import get_main_message
from keyboards import get_settings_keyboard
from callbacks import ToggleCallback
from services import UserService

router = Router()


@router.callback_query(F.data == NavigationAction.SETTINGS)
@inject
async def settings_callback_handler(
        callback: types.CallbackQuery,
        user_service: UserService = Provide[Deps.services.user]
):
    user = await user_service.get_user_with_subscriptions()
    text = get_main_message(user)
    reply_markup = get_settings_keyboard(user)
    await callback.message.edit_text(
        text=text,
        reply_markup=reply_markup,
    )
    await callback.answer()

@router.callback_query(ToggleCallback.filter(F.flag_name == ToggleEnum.UPCOMING))
@inject
async def toggle_updates_handler(
        callback: types.CallbackQuery,
        user_service: UserService = Provide[Deps.services.user],
):
    await user_service.toggle_notify_upcoming_lessons()
    await settings_callback_handler(callback=callback)


@router.callback_query(ToggleCallback.filter(F.flag_name == ToggleEnum.CHANGES))
@inject
async def toggle_updates_handler(
        callback: types.CallbackQuery,
        user_service: UserService = Provide[Deps.services.user],
):
    await user_service.toggle_notify_schedule_updates()
    await settings_callback_handler(callback=callback)
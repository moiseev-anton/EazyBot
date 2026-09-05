from aiogram import F, Router, types
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import NavigationAction, ScheduleStyle, ToggleEnum
from aiogram.types import InputRichMessage

from messages import add_rich_keyboard, get_main_message, get_rich_settings_message
from keyboards import get_settings_keyboard
from callbacks import ToggleCallback
from services import TelegramUiPreferences, UserService

router = Router()


@router.callback_query(F.data == NavigationAction.SETTINGS)
@inject
async def settings_callback_handler(
        callback: types.CallbackQuery,
        user_service: UserService = Provide[Deps.services.user],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    user = await user_service.get_user_with_subscriptions()
    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    reply_markup = get_settings_keyboard(user, schedule_style)
    if schedule_style == ScheduleStyle.RICH:
        text = add_rich_keyboard(get_rich_settings_message(user), reply_markup)
        reply_markup = None
    else:
        text = get_main_message(user)
    await callback.message.edit_text(
        text=text if isinstance(text, str) else None,
        rich_message=text if isinstance(text, InputRichMessage) else None,
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

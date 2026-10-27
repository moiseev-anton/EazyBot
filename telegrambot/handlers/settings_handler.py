from aiogram import F, Router, types
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import NavigationAction, ScheduleStyle
from aiogram.types import InputRichMessage

from messages import add_rich_keyboard, get_main_message, get_rich_settings_message
from keyboards import get_settings_keyboard
from callbacks import ToggleCallback, NotificationCallback
from services.notification_preferences import NotificationPreferences
from services import TelegramUiPreferences, UserService
from telegram_helpers import edit_message_with_retry

router = Router()


@router.callback_query(F.data == NavigationAction.SETTINGS)
@inject
async def settings_callback_handler(
        callback: types.CallbackQuery,
        user_service: UserService = Provide[Deps.services.user],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
        notification_preferences: NotificationPreferences = Provide[Deps.services.notification_preferences],
        preferences: dict | None = None,
):
    user = await user_service.get_user_with_subscriptions()
    if preferences is None:
        preferences = await notification_preferences.get_preferences(str(callback.from_user.id))
    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    reply_markup = get_settings_keyboard(user, preferences, schedule_style)
    if schedule_style == ScheduleStyle.RICH:
        text = add_rich_keyboard(get_rich_settings_message(user), reply_markup)
        reply_markup = None
    else:
        text = get_main_message(user)
    await edit_message_with_retry(callback.message,
        text=text if isinstance(text, str) else None,
        rich_message=text if isinstance(text, InputRichMessage) else None,
        reply_markup=reply_markup,
    )

@router.callback_query(NotificationCallback.filter())
@inject
async def notification_toggle_handler(
        callback: types.CallbackQuery,
        callback_data: NotificationCallback,
        notification_preferences: NotificationPreferences = Provide[Deps.services.notification_preferences],
):
    preferences = await notification_preferences.set_enabled(
        str(callback.from_user.id), callback_data.notification_type,
        callback_data.enabled, callback_data.version,
    )
    await settings_callback_handler(callback=callback, preferences=preferences)


@router.callback_query(ToggleCallback.filter())
async def legacy_notification_toggle_handler(
        callback: types.CallbackQuery,
):
    # Old messages lack the desired state/version: only replace their keyboard.
    await settings_callback_handler(callback=callback)

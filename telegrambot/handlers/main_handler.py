from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InputRichMessage
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from callbacks import ScheduleUiCallback
from enums import NavigationAction, ScheduleStyle
from keyboards import get_main_keyboard
from messages import add_rich_footer, add_rich_keyboard, get_main_message, get_rich_main_message
from services import TelegramUiPreferences, UserService
from telegram_helpers import edit_message_with_retry

router = Router()

@inject
async def build_main_menu_content(
        telegram_user_id: int,
        user_service: UserService = Provide[Deps.services.user],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
) -> tuple[str | InputRichMessage, InlineKeyboardMarkup | None]:
    user = await user_service.get_user_with_subscriptions()
    sub_id = endpoint = None
    if user.subscriptions:
        first_subscription = user.subscriptions[0]
        sub_id = first_subscription.id
        endpoint = first_subscription.endpoint

    schedule_style = await telegram_ui_preferences.get_schedule_style(telegram_user_id)
    reply_markup = get_main_keyboard(sub_id, endpoint, schedule_style)
    if schedule_style == ScheduleStyle.RICH:
        text = add_rich_footer(
            add_rich_keyboard(
                get_rich_main_message(user, add_bottom_spacer=True),
                reply_markup,
            ),
            "Вернуть старый UI можно в настройках.",
        )
        reply_markup = None
    else:
        text = get_main_message(user)
    return text, reply_markup


@router.callback_query(F.data == NavigationAction.MAIN)
async def main_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    text, reply_markup = await build_main_menu_content(callback.from_user.id)
    await edit_message_with_retry(callback.message,
        text=text if isinstance(text, str) else None,
        rich_message=text if isinstance(text, InputRichMessage) else None,
        reply_markup=reply_markup,
    )

    await state.clear()


@router.message(Command(NavigationAction.MAIN))
async def main_command_handler(
        message: types.Message,
        state: FSMContext,
):
    text, reply_markup = await build_main_menu_content(message.from_user.id)
    if isinstance(text, InputRichMessage):
        await message.answer_rich(text, reply_markup=reply_markup)
    else:
        await message.answer(text=text, reply_markup=reply_markup)

    await state.clear()


@router.message(Command("legacy"))
@inject
async def legacy_command_handler(
        message: types.Message,
        state: FSMContext,
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    await telegram_ui_preferences.set_schedule_style(
        message.from_user.id,
        ScheduleStyle.LEGACY,
    )
    text, reply_markup = await build_main_menu_content(message.from_user.id)
    await message.answer(text=text, reply_markup=reply_markup)
    await state.clear()


@router.callback_query(ScheduleUiCallback.filter())
@inject
async def schedule_ui_handler(
        callback: types.CallbackQuery,
        callback_data: ScheduleUiCallback,
        state: FSMContext,
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    await telegram_ui_preferences.set_schedule_style(
        callback.from_user.id,
        ScheduleStyle(callback_data.style),
    )
    text, reply_markup = await build_main_menu_content(callback.from_user.id)
    await edit_message_with_retry(callback.message,
        text=text if isinstance(text, str) else None,
        rich_message=text if isinstance(text, InputRichMessage) else None,
        reply_markup=reply_markup,
    )
    await state.clear()

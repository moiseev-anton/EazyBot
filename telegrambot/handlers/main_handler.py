from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import NavigationAction
from managers import KeyboardManager, MessageManager
from services import UserService

router = Router()

@inject
async def build_main_menu_content(
        user_service: UserService = Provide[Deps.services.user],
) -> tuple[str, InlineKeyboardMarkup]:
    user = await user_service.get_user_with_subscriptions()
    sub_id = endpoint = None
    if user.subscriptions:
        first_subscription = user.subscriptions[0]
        sub_id = first_subscription.id
        endpoint = first_subscription.endpoint

    text = MessageManager.get_main_message(user)
    reply_markup = KeyboardManager.get_main_keyboard(sub_id, endpoint)
    return text, reply_markup


@router.callback_query(F.data == NavigationAction.MAIN)
async def main_callback_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
):
    text, reply_markup = await build_main_menu_content()
    await callback.message.edit_text(
        text=text,
        reply_markup=reply_markup,
    )

    await state.clear()
    await callback.answer()


@router.message(Command(NavigationAction.MAIN))
async def main_command_handler(
        message: types.Message,
        state: FSMContext,
):
    text, reply_markup = await build_main_menu_content()
    await message.answer(
        text=text,
        reply_markup=reply_markup,
    )

    await state.clear()
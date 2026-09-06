import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputRichMessage
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import Branch, ScheduleStyle
from states import get_state_data
from messages import add_rich_keyboard, get_rich_selected_message, get_selected_msg
from callbacks import EntityCallback
from keyboards import get_actions_keyboard
from services import GroupService, SubscriptionService, TeacherService, TelegramUiPreferences
from states import ActionStates
from telegram_helpers import edit_message_with_retry

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(EntityCallback.filter())
@inject
async def entity_handler(
        callback: types.CallbackQuery,
        callback_data: EntityCallback,
        state: FSMContext,
        teacher_service: TeacherService = Provide[Deps.services.teacher],
        group_service: GroupService = Provide[Deps.services.group],
        subscription_service: SubscriptionService = Provide[Deps.services.subscription],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    data = await get_state_data(state, required_keys=("branch",))
    branch = data["branch"]

    obj_id = callback_data.id
    await state.update_data(obj_id=obj_id)

    match branch:
        case Branch.TEACHERS:
            obj = teacher_service.get_teacher(obj_id)

        case Branch.GROUPS:
            obj = group_service.get_group(obj_id)

        case _:
            ValueError(f"Unknown navigation branch: {branch}")

    subscription = await subscription_service.get_subscription_by_target(obj)
    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)

    keyboard = get_actions_keyboard(obj, subscription, schedule_style)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_selected_message(obj, branch, subscription is not None), keyboard
        )
        reply_markup = None
    else:
        content = get_selected_msg(obj, subscription)
        reply_markup = keyboard
    await edit_message_with_retry(callback.message,
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
    )
    await state.set_state(ActionStates.choosing_action)

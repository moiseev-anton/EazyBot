import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputRichMessage
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import Branch, ScheduleStyle, SubscriptionAction
from messages import add_rich_keyboard, ALREADY_HAS_SUBSCRIPTION_WARNING, get_rich_subscription_replacement_warning
from states import get_state_data
from handlers.entity_handler import entity_handler
from handlers.main_handler import main_callback_handler
from keyboards import BACK_HOME_KB, CONFIRM_KB
from callbacks import EntityCallback, SubscriptionCallback
from services import GroupService, SubscriptionService, TeacherService, TelegramUiPreferences
from states import ActionStates
from telegram_helpers import edit_message_with_retry

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(SubscriptionCallback.filter(F.action == SubscriptionAction.SUBSCRIBE))
@inject
async def subscribe_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        subscription_service: SubscriptionService = Provide[Deps.services.subscription],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    if await subscription_service.has_any_subscriptions():
        schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
        content = (
            add_rich_keyboard(get_rich_subscription_replacement_warning(), BACK_HOME_KB)
            if schedule_style == ScheduleStyle.RICH else ALREADY_HAS_SUBSCRIPTION_WARNING
        )
        await edit_message_with_retry(callback.message,
            text=content if isinstance(content, str) else None,
            rich_message=content if isinstance(content, InputRichMessage) else None,
            reply_markup=None if isinstance(content, InputRichMessage) else CONFIRM_KB,
        )
        await state.set_state(ActionStates.waiting_sub_confirm)

    else:
        await create_subscription_handler(callback, state)


@inject
async def create_subscription_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        teacher_service: TeacherService = Provide[Deps.services.teacher],
        group_service: GroupService = Provide[Deps.services.group],
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    data = await get_state_data(state, required_keys=('branch', 'obj_id'))
    branch = data["branch"]
    obj_id = data["obj_id"]

    match branch:
        case Branch.TEACHERS:
            obj = teacher_service.get_teacher(obj_id)
        case Branch.GROUPS:
            obj = group_service.get_group(obj_id)
        case _:
            raise ValueError()

    new_sub = await subscription_service.subscribe(obj)

    await callback.answer("Подписка создана!👌")
    await main_callback_handler(callback, state)
    return


@router.callback_query(SubscriptionCallback.filter(F.action == SubscriptionAction.UNSUBSCRIBE))
@inject
async def unsubscribe_handler(
        callback: types.CallbackQuery,
        callback_data: SubscriptionCallback,
        state: FSMContext,
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    sub_id = callback_data.sub_id
    await subscription_service.unsubscribe(sub_id)
    await callback.answer(" Подписка удалена!👌")

    current_state = await state.get_state()
    if current_state == ActionStates.choosing_action:
        data = await get_state_data(state, required_keys=("obj_id",))
        fake_callback_data = EntityCallback(id=data["obj_id"])
        await entity_handler(callback, fake_callback_data, state)
    else:
        await main_callback_handler(callback, state)

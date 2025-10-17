import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from dependencies import Deps
from handlers.main_handler import main_handler
from handlers.entity_handler import entity_handler
from managers import MessageManager
from managers.keyboard_manager import EntityCallback, KeyboardManager, SubscriptionCallback
from services import GroupService, SubscriptionService, TeacherService
from states import ActionStates, GroupStates, TeacherStates

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(SubscriptionCallback.filter(F.action == 'subscribe'))
@inject
async def subscribe_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    if await subscription_service.has_any_subscriptions():

        await callback.message.edit_text(
            text=MessageManager.ALREADY_HAS_SUBSCRIPTION_WARNING,
            reply_markup=KeyboardManager.confirm,
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
    data = await state.get_data()
    branch = data.get("branch")
    obj_id = data.get("obj_id")

    match branch:
        case "teachers":
            obj = teacher_service.get_teacher(obj_id)
        case "groups":
            obj = group_service.get_group(obj_id)

    new_sub = await subscription_service.subscribe(obj)

    await callback.answer("✅ Успешно!")
    await main_handler(callback, state)
    return


@router.callback_query(SubscriptionCallback.filter(F.action == 'unsubscribe'))
@inject
async def unsubscribe_handler(
        callback: types.CallbackQuery,
        callback_data: SubscriptionCallback,
        state: FSMContext,
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    sub_id = callback_data.sub_id
    await subscription_service.unsubscribe(sub_id)

    current_state = await state.get_state()
    data = await state.get_data()
    if current_state == ActionStates.choosing_action:
        fake_callback_data = EntityCallback(id=data.get("obj_id"))
        await entity_handler(callback, fake_callback_data, state)
    else:
        await main_handler(callback, state)

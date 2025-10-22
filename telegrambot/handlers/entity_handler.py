import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from dependencies import Deps
from enums import Branch
from fsm_utils import get_state_data
from managers import KeyboardManager, MessageManager
from managers.button_manager import EntityCallback
from services import GroupService, SubscriptionService, TeacherService
from states import ActionStates

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
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    data = await state.get_data()
    branch = data.get("branch")
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

    await callback.message.edit_text(
        text=MessageManager.get_selected_msg(obj, subscription),
        reply_markup=KeyboardManager.get_actions_keyboard(obj, subscription),
    )
    await state.set_state(ActionStates.choosing_action)
    await callback.answer()

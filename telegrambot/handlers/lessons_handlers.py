import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from dto import DateSpanDTO
from dto.base_dto import SubscriptableDTO
from enums import Branch, EntitySource, ModeEnum
from fsm_utils import get_state_data
from managers import KeyboardManager, MessageManager
from managers.button_manager import LessonsCallback
from services import GroupService, LessonService, SubscriptionService, TeacherService
from states import ActionStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(LessonsCallback.filter(F.source == EntitySource.SUBSCRIPTION))
@inject
async def lessons_handler(
        callback: types.CallbackQuery,
        callback_data: LessonsCallback,
        lesson_service: LessonService = Provide[Deps.services.lesson],
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    mode, shift = callback_data.mode, callback_data.shift

    subs = await subscription_service.get_user_subscriptions()
    if not subs:
        raise Exception('No subscriptions found')

    target_object: SubscriptableDTO = subs[0].object
    date_span = DateSpanDTO.from_mode(mode, shift)
    lessons = await lesson_service.get_lessons(target_object, date_span)
    new_text = MessageManager.format_schedule(target_object, lessons, date_span)

    if new_text == callback.message.html_text:
        await callback.answer("💫 Обновлено")
        return

    await callback.message.edit_text(
        text=new_text,
        reply_markup=KeyboardManager.get_schedule_keyboard(callback_data, date_span),
    )
    await callback.answer()


@router.callback_query(LessonsCallback.filter(F.source == EntitySource.CONTEXT))
@inject
async def lessons_handler(
        callback: types.CallbackQuery,
        callback_data: LessonsCallback,
        state: FSMContext,
        lesson_service: LessonService = Provide[Deps.services.lesson],
        teacher_service: TeacherService = Provide[Deps.services.teacher],
        group_service: GroupService = Provide[Deps.services.group],
):
    data = await get_state_data(state, required_keys=('branch', 'obj_id'))
    branch = data['branch']
    obj_id = data['obj_id']

    match branch:
        case Branch.TEACHERS:
            target_object = teacher_service.get_teacher(obj_id)

        case Branch.GROUPS:
            target_object = group_service.get_group(obj_id)

        case _:
            raise ValueError(f"Unknown navigation branch: {branch}")

    schedule_mode = ModeEnum(callback_data.mode)
    date_span = DateSpanDTO.from_mode(schedule_mode, callback_data.shift)

    lessons = await lesson_service.get_lessons(target_object, date_span)

    await callback.message.edit_text(
        text=MessageManager.format_schedule(target_object, lessons, date_span),
        reply_markup=KeyboardManager.back_home,
    )
    await state.set_state(ActionStates.reading_schedule)
    await callback.answer()

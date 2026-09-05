import logging

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from callbacks import LessonsCallback, RichLessonsCallback
from dependencies import Deps
from dto import DateSpanDTO, LessonDTO
from dto.base_dto import SubscriptableDTO
from enums import Branch, EntitySource
from keyboards import get_schedule_keyboard
from messages import add_rich_keyboard, get_rich_schedule_msg, get_schedule_msg
from schedule_view_modes import ScheduleMode
from services import GroupService, LessonService, SubscriptionService, TeacherService
from states import ActionStates, get_state_data

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(LessonsCallback.filter(F.source == EntitySource.SUBSCRIPTION))
@router.callback_query(RichLessonsCallback.filter(F.source == EntitySource.SUBSCRIPTION))
@inject
async def lessons_handler(
        callback: types.CallbackQuery,
        callback_data: LessonsCallback | RichLessonsCallback,
        lesson_service: LessonService = Provide[Deps.services.lesson],
        subscription_service: SubscriptionService = Provide[Deps.services.subscription]
):
    subs = await subscription_service.get_user_subscriptions()
    if not subs:
        raise Exception('No subscriptions found')

    mode = ScheduleMode(callback_data.mode)
    shift = callback_data.shift
    date_span = mode.get_span(shift=shift)

    target_object: SubscriptableDTO = subs[0].object
    lessons = await lesson_service.get_lessons(target_object, date_span)
    prev_page, next_page = mode.get_page_range(shift=shift)
    message_changed = await _edit_schedule_message(
        callback=callback,
        callback_data=callback_data,
        target_obj=target_object,
        lessons=lessons,
        date_span=date_span,
        prev_page=prev_page,
        next_page=next_page,
    )
    await callback.answer("💫 Обновлено" if not message_changed else None)


@router.callback_query(LessonsCallback.filter(F.source == EntitySource.CONTEXT))
@router.callback_query(RichLessonsCallback.filter(F.source == EntitySource.CONTEXT))
@inject
async def context_lessons_handler(
        callback: types.CallbackQuery,
        callback_data: LessonsCallback | RichLessonsCallback,
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

    mode = ScheduleMode(callback_data.mode)
    shift = callback_data.shift
    date_span = mode.get_span(shift=shift)
    lessons = await lesson_service.get_lessons(target_object, date_span)
    prev_page, next_page = mode.get_page_range(shift=shift)
    message_changed = await _edit_schedule_message(
        callback=callback,
        callback_data=callback_data,
        target_obj=target_object,
        lessons=lessons,
        date_span=date_span,
        prev_page=prev_page,
        next_page=next_page,
    )
    await state.set_state(ActionStates.reading_schedule)
    await callback.answer("Обновлено" if not message_changed else None)


async def _edit_schedule_message(
        callback: types.CallbackQuery,
        callback_data: LessonsCallback | RichLessonsCallback,
        target_obj: SubscriptableDTO,
        lessons: list[LessonDTO],
        date_span: DateSpanDTO,
        prev_page: int | None,
        next_page: int | None,
) -> bool:
    reply_markup = get_schedule_keyboard(callback_data, prev_page, next_page)

    try:
        if isinstance(callback_data, RichLessonsCallback):
            await callback.message.edit_text(
                rich_message=add_rich_keyboard(
                    get_rich_schedule_msg(target_obj, lessons, date_span), reply_markup
                ),
            )
        else:
            await callback.message.edit_text(
                text=get_schedule_msg(target_obj, lessons, date_span),
                reply_markup=reply_markup,
            )
        return True
    except TelegramBadRequest as error:
        if "message is not modified" not in str(error).lower():
            raise
        return False

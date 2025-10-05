from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from dependencies import Deps
from managers.keyboard_manager import ActionCallback
from states import TeacherStates, FacultyStates

router = Router()


# @router.callback_query(ActionCallback.filter((F.action == "schedule") & (F.obj_type == "group")))
# async def group_schedule_action_handler(
#         callback: types.CallbackQuery,
#         callback_data: ActionCallback,
#         state: FSMContext,
#         deps: Deps
# ):
#     obj_type = callback_data.obj_type
#     group_id = callback_data.id
#     user = callback.from_user
#
#     state_data = await state.get_data()
#     faculty_id = state_data.get("faculty_id")
#     course_id = state_data.get("course_id")
#     group_data = deps.keyboard_data_store().get_group(faculty_id, course_id, group_id)
#
#     lessons_doc = await deps.services.lesson(user=user).get_actual_lessons(obj_type, group_id)
#     text = deps.managers.message().format_group_schedule(group_title=group_data.get("title"), schedule_data=lessons_doc)
#
#     await callback.message.edit_text(
#         text=text,
#         reply_markup=deps.managers.keyboard().back_home,
#     )
#     await state.set_state(FacultyStates.action)
#     await callback.answer()
#
#
# @router.callback_query(ActionCallback.filter((F.action == "schedule") & (F.obj_type == "teacher")))
# async def teacher_schedule_action_handler(
#     callback: types.CallbackQuery,
#     callback_data: ActionCallback,
#     state: FSMContext,
#     deps: Deps,
# ):
#     obj_type = callback_data.obj_type
#     teacher_id = callback_data.id
#     user = callback.from_user
#
#     state_data = await state.get_data()
#     letter = state_data.get("letter")
#     teacher_data = deps.keyboard_data_store().get_teacher(letter, teacher_id)
#
#     lessons_data = await deps.services.lesson(user=user).get_actual_lessons(obj_type, teacher_id)
#     text = deps.managers.message().format_teacher_schedule(teacher_data.get('short_name'), lessons_data)
#
#     await callback.message.edit_text(
#         text=text,
#         reply_markup=deps.managers.keyboard().back_home
#     )
#     await state.set_state(TeacherStates.action)
#     await callback.answer()

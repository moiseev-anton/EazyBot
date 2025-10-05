import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from dependencies import Deps
from handlers.error_handler import handle_error
from handlers.main_handler import main_handler
from handlers.group_handlers import (
    faculties_handler,
    faculty_grades_handler,
    course_groups_handler,
    FacultyCallback,
    GradeCallback, group_selected_handler
)
from handlers.teacher_handlers import alphabet_handler, teachers_bucket_handler, teacher_selected_handler
from managers.keyboard_manager import GroupCallback, TeacherCallback, AlphabetCallback
from states import FacultyStates, TeacherStates

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "back")
async def back_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    current_state = await state.get_state()
    data = await state.get_data()

    # Навигация по факультетам
    match current_state:
        # Возврат от выбора курса к выбору факультета
        case FacultyStates.choosing_course.state:
            await faculties_handler(callback, state)
            return

        # Возврат от выбора группы к выбору курса
        case FacultyStates.choosing_group.state:
            faculty_id = data.get("faculty_id")
            fake_callback_data = FacultyCallback(faculty_id=faculty_id)
            await faculty_grades_handler(callback, fake_callback_data, state)
            return

        # Возврат от выбора действия к выбору группы
        case FacultyStates.choosing_action.state:
            grade = data.get("grade")
            fake_callback_data = GradeCallback(grade=grade)
            await course_groups_handler(callback, fake_callback_data, state)
            return

        # Возврат к выбору действия группы
        case FacultyStates.action.state:
            group_id = data.get("group_id")
            fake_callback_data = GroupCallback(group_id=group_id)
            await group_selected_handler(callback, fake_callback_data, state)
            return

        # Возврат от выбора преподавателя к выбору буквы
        case TeacherStates.choosing_teacher.state:
            await alphabet_handler(callback, state)
            return

        # Возврат от выбора действия к выбору преподавателя
        case TeacherStates.choosing_action.state:
            letter = data.get("letter")
            fake_callback_data = AlphabetCallback(letter=letter)
            await teachers_bucket_handler(callback, fake_callback_data, state)
            return

        # Возврат к выбору действия преподавателя
        case TeacherStates.action.state:
            teacher_id = data.get("teacher_id")
            fake_callback_data = TeacherCallback(teacher_id=teacher_id)
            await teacher_selected_handler(callback, fake_callback_data, state)
            return

        case _:
            await main_handler(callback, state)
            # await handle_error(callback, state)


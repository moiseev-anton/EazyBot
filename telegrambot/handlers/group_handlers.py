import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import Branch, NavigationAction
from fsm_utils import get_state_data
from managers import KeyboardManager, MessageManager
from managers.button_manager import FacultyCallback, GradeCallback
from services import GroupService
from states import GroupStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == NavigationAction.FACULTIES)
@inject
async def faculties_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        group_service: GroupService = Provide[Deps.services.group],
):
    """
    Первый уровень навигации групп.
    Ответ - клавиатура с факультетами.
    """
    await state.update_data(branch=Branch.GROUPS)

    faculties = group_service.get_faculties()

    await callback.message.edit_text(
        text=MessageManager.FACULTY_CHOOSING,
        reply_markup=KeyboardManager.get_faculties_keyboard(faculties),
    )
    await state.set_state(GroupStates.choosing_faculty)
    await callback.answer()


@router.callback_query(FacultyCallback.filter())
@inject
async def faculty_grades_handler(
        callback: types.CallbackQuery,
        callback_data: FacultyCallback,
        state: FSMContext,
        group_service: GroupService = Provide[Deps.services.group],
):
    """
    Второй уровень навигации групп.
    Ответ - клавиатура с курсами выбранного факультета.
    """
    faculty_id = callback_data.faculty_id
    await state.update_data(faculty_id=faculty_id)

    faculty = group_service.get_faculty(faculty_id)
    grades = group_service.get_grades_for_faculty(faculty_id)

    await callback.message.edit_text(
        text=MessageManager.get_grade_choosing_msg(faculty),
        reply_markup=KeyboardManager.get_grades_keyboard(grades),
    )
    await state.set_state(GroupStates.choosing_grade)
    await callback.answer()


@router.callback_query(GradeCallback.filter())
@inject
async def course_groups_handler(
        callback: types.CallbackQuery,
        callback_data: GradeCallback,
        state: FSMContext,
        group_service: GroupService = Provide[Deps.services.group],
):
    """
    Третий уровень навигации групп.
    Ответ - клавиатура с группами выбранного факультета и курса.
    """
    data = await get_state_data(state, required_keys=("faculty_id",))
    faculty_id = data["faculty_id"]

    chosen_grade = callback_data.grade
    await state.update_data(grade=chosen_grade)

    faculty = group_service.get_faculty(faculty_id)
    groups = group_service.get_groups_for_faculty_grade(faculty_id, chosen_grade)

    await callback.message.edit_text(
        text=MessageManager.get_group_choosing_msg(faculty, chosen_grade),
        reply_markup=KeyboardManager.get_groups_keyboard(groups),
    )
    await state.set_state(GroupStates.choosing_group)
    await callback.answer()

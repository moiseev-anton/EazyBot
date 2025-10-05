import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from managers import MessageManager, KeyboardManager
from managers.keyboard_manager import (
    FacultyCallback,
    GradeCallback,
    GroupCallback
)
from services import GroupService
from states import FacultyStates

logger = logging.getLogger(__name__)


router = Router()


@router.callback_query(F.data == "faculties")
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
    await state.update_data(branch="groups")

    faculties = group_service.get_faculties()

    await callback.message.edit_text(
        text=MessageManager.get_faculty_choosing_msg(),
        reply_markup=KeyboardManager.get_faculties_keyboard(faculties),
    )
    await state.set_state(FacultyStates.choosing_faculty)
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
    await state.set_state(FacultyStates.choosing_course)
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
    chosen_grade = callback_data.grade
    data = await state.get_data()
    faculty_id = data.get("faculty_id")
    await state.update_data(grade=chosen_grade)

    faculty = group_service.get_faculty(faculty_id)
    groups = group_service.get_groups_for_faculty_grade(faculty_id, chosen_grade)

    await callback.message.edit_text(
        text=MessageManager.get_group_choosing_msg(faculty, chosen_grade),
        reply_markup=KeyboardManager.get_groups_keyboard(groups),
    )
    await state.set_state(FacultyStates.choosing_group)
    await callback.answer()


@router.callback_query(GroupCallback.filter())
@inject
async def group_selected_handler(
    callback: types.CallbackQuery,
    callback_data: GroupCallback,
    state: FSMContext,
    group_service: GroupService = Provide[Deps.services.group],
):
    group_id = callback_data.group_id
    await state.update_data(group_id=group_id)

    group = group_service.get_group(group_id)

    await callback.message.edit_text(
        text=MessageManager.get_selected_group_msg(group),
        reply_markup=KeyboardManager.get_actions_keyboard(group),
    )
    await state.set_state(FacultyStates.choosing_action)
    await callback.answer()

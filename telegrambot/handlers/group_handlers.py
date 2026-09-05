import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputRichMessage
from dependency_injector.wiring import inject, Provide

from callbacks import FacultyCallback, GradeCallback
from dependencies import Deps
from enums import Branch, NavigationAction, ScheduleStyle
from keyboards import get_faculties_keyboard, get_grades_keyboard, get_groups_keyboard
from messages import add_rich_keyboard, FACULTY_CHOOSING, get_grade_choosing_msg, get_group_choosing_msg, get_rich_choosing_message
from services import GroupService, TelegramUiPreferences
from states import get_state_data, GroupStates

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == NavigationAction.FACULTIES)
@inject
async def faculties_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        group_service: GroupService = Provide[Deps.services.group],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    """
    Первый уровень навигации групп.
    Ответ - клавиатура с факультетами.
    """
    await state.update_data(branch=Branch.GROUPS)

    faculties = group_service.get_faculties()

    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    keyboard = get_faculties_keyboard(faculties)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_choosing_message("Группы", "Выберите факультет."), keyboard
        )
        reply_markup = None
    else:
        content = FACULTY_CHOOSING
        reply_markup = keyboard
    await callback.message.edit_text(
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
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
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    """
    Второй уровень навигации групп.
    Ответ - клавиатура с курсами выбранного факультета.
    """
    faculty_id = callback_data.faculty_id
    await state.update_data(faculty_id=faculty_id)

    faculty = group_service.get_faculty(faculty_id)
    grades = group_service.get_grades_for_faculty(faculty_id)

    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    keyboard = get_grades_keyboard(grades)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_choosing_message(faculty.title, "Выберите курс."), keyboard
        )
        reply_markup = None
    else:
        content = get_grade_choosing_msg(faculty)
        reply_markup = keyboard
    await callback.message.edit_text(
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
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
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
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

    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    keyboard = get_groups_keyboard(groups)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_choosing_message(
                faculty.title,
                "Выберите группу.",
                context=f"{chosen_grade} курс",
            ),
            keyboard,
        )
        reply_markup = None
    else:
        content = get_group_choosing_msg(faculty, chosen_grade)
        reply_markup = keyboard
    await callback.message.edit_text(
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
    )
    await state.set_state(GroupStates.choosing_group)
    await callback.answer()

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from enums import Branch, NavigationAction
from handlers.entity_handler import entity_handler
from handlers.group_handlers import course_groups_handler, faculties_handler, faculty_grades_handler
from handlers.main_handler import main_handler
from handlers.subscription_handlers import create_subscription_handler
from handlers.teacher_handlers import alphabet_handler, teachers_bucket_handler
from managers.keyboard_manager import AlphabetCallback, EntityCallback, FacultyCallback, GradeCallback
from states import ActionStates, GroupStates, TeacherStates

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == NavigationAction.BACK)
async def back_handler(
        callback: types.CallbackQuery, state: FSMContext
):
    current_state = await state.get_state()
    data = await state.get_data()

    # Возврат от подтверждения подписки к выбору действия (с группой/учителем)
    if current_state == ActionStates.waiting_sub_confirm.state:
        obj_id = data.get("obj_id")
        fake_callback_data = EntityCallback(id=obj_id)
        await entity_handler(callback, fake_callback_data, state)
        return

    branch = data.get("branch")

    match branch:
        case Branch.TEACHERS:
            match current_state:
                # Возврат от выбора преподавателя к выбору буквы
                case TeacherStates.choosing_teacher.state:
                    await alphabet_handler(callback, state)
                    return

                # Возврат от выбора действия к выбору преподавателя
                case ActionStates.choosing_action.state:
                    letter = data.get("letter")
                    fake_callback_data = AlphabetCallback(letter=letter)
                    await teachers_bucket_handler(callback, fake_callback_data, state)
                    return

                case _:
                    await main_handler(callback, state)
                    return
                    # await handle_error(callback, state)

        case Branch.GROUPS:
            match current_state:
                # Возврат от выбора курса к выбору факультета
                case GroupStates.choosing_grade.state:
                    await faculties_handler(callback, state)
                    return

                # Возврат от выбора группы к выбору курса
                case GroupStates.choosing_group.state:
                    faculty_id = data.get("faculty_id")
                    fake_callback_data = FacultyCallback(faculty_id=faculty_id)
                    await faculty_grades_handler(callback, fake_callback_data, state)
                    return

                # Возврат от выбора действия к выбору группы
                case ActionStates.choosing_action.state:
                    grade = data.get("grade")
                    fake_callback_data = GradeCallback(grade=grade)
                    await course_groups_handler(callback, fake_callback_data, state)
                    return

                case _:
                    await main_handler(callback, state)
                    # await handle_error(callback, state)
                    return

        case _:
            await main_handler(callback, state)
            # await handle_error(callback, state)
            return


@router.callback_query(F.data == NavigationAction.CONFIRM)
async def confirm_handler(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    match current_state:
        case ActionStates.waiting_sub_confirm.state:
            await create_subscription_handler(callback, state)

        case _:
            await main_handler(callback, state)
            # await handle_error(callback, state)
            return

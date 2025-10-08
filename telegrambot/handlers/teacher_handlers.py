import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from handlers.error_handler import handle_error
from managers import MessageManager
from managers.keyboard_manager import AlphabetCallback, TeacherCallback, EntityCallback, KeyboardManager
from services import TeacherService, UserService
from states import TeacherStates

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "alphabet")
@inject
async def alphabet_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    teacher_service: TeacherService = Provide[Deps.services.teacher]
):
    """
    Первый уровень навигации преподавателей.
    Ответ - клавиатура с алфавитным указателем.
    """
    await state.update_data(branch="teachers")

    letters = teacher_service.get_letters()

    await callback.message.edit_text(
        text=MessageManager.get_letter_choosing_msg(),
        reply_markup=KeyboardManager.get_alphabet_keyboard(letters),
    )
    await state.set_state(TeacherStates.choosing_letter)
    await callback.answer()


@router.callback_query(AlphabetCallback.filter())
@inject
async def teachers_bucket_handler(
    callback: types.CallbackQuery,
    callback_data: AlphabetCallback,
    state: FSMContext,
    teacher_service: TeacherService = Provide[Deps.services.teacher],
):
    """
    Второй уровень навигации преподавателей.
    Ответ - клавиатура с преподавателями на конкретную букву.
    """
    letter = callback_data.letter
    await state.update_data(letter=letter)

    teachers = teacher_service.get_teachers(letter)

    await callback.message.edit_text(
        text=MessageManager.get_teacher_choosing_msg(),
        reply_markup=KeyboardManager.get_teachers_keyboard(teachers),
    )
    await state.set_state(TeacherStates.choosing_teacher)
    await callback.answer()


@router.callback_query(TeacherCallback.filter())
@inject
async def teacher_selected_handler(
    callback: types.CallbackQuery,
    callback_data: TeacherCallback,
    state: FSMContext,
    teacher_service: TeacherService = Provide[Deps.services.teacher],
):
    teacher_id = callback_data.teacher_id
    await state.update_data(teacher_id=teacher_id)
    teacher = teacher_service.get_teacher(teacher_id)
    # TODO: Добавить получение текущих подписок пользователя
    #  и уже потом формировать клавиатуру (для кнопки подписаться/отписаться)
    await callback.message.edit_text(
        text=MessageManager.get_selected_teacher_msg(teacher),
        reply_markup=KeyboardManager.get_actions_keyboard(teacher),
    )
    await state.set_state(TeacherStates.choosing_action)
    await callback.answer()


@router.callback_query(EntityCallback.filter())
async def entity_handler(
    callback: types.CallbackQuery,
    callback_data: EntityCallback,
    state: FSMContext,
    deps: Deps,
):
    data = await state.get_data()
    branch = data.get("branch")

    match branch:
        case "teachers":
            teacher_id = callback_data.id
            await state.update_data(teacher_id=teacher_id)
            letter = data.get("letter")
            teacher_data = deps.keyboard_data_store().get_teacher(letter, teacher_id)
            text = deps.managers.message().get_selected_teacher_msg(teacher_data)
            keyboard = deps.managers.keyboard().get_actions_keyboard("teacher", teacher_data)
        case "groups":
            group_id = callback_data.id
            await state.update_data(group_id=group_id)
            faculty_id = data.get("faculty_id")
            course_id = data.get("course_id")
            group_data = deps.keyboard_data_store().get_group(faculty_id, course_id, group_id)
            text = deps.managers.message().get_selected_group_msg(group_data)
            keyboard = deps.managers.keyboard().get_actions_keyboard("group", group_data)

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
    )
    await state.set_state(TeacherStates.choosing_action)
    await callback.answer()

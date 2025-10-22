import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import Branch
from managers import KeyboardManager, MessageManager
from managers.button_manager import AlphabetCallback
from services import TeacherService
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
    await state.update_data(branch=Branch.TEACHERS)

    letters = teacher_service.get_letters()

    await callback.message.edit_text(
        text=MessageManager.LETTER_CHOOSING,
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
        text=MessageManager.TEACHERS_CHOOSING,
        reply_markup=KeyboardManager.get_teachers_keyboard(teachers),
    )
    await state.set_state(TeacherStates.choosing_teacher)
    await callback.answer()

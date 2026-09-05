import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InputRichMessage
from dependency_injector.wiring import inject, Provide

from dependencies import Deps
from enums import Branch, ScheduleStyle
from messages import add_rich_keyboard, LETTER_CHOOSING, TEACHERS_CHOOSING, get_rich_choosing_message
from keyboards import get_alphabet_keyboard, get_teachers_keyboard
from callbacks import AlphabetCallback
from services import TeacherService, TelegramUiPreferences
from states import TeacherStates

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "alphabet")
@inject
async def alphabet_handler(
        callback: types.CallbackQuery,
        state: FSMContext,
        teacher_service: TeacherService = Provide[Deps.services.teacher],
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    """
    Первый уровень навигации преподавателей.
    Ответ - клавиатура с алфавитным указателем.
    """
    await state.update_data(branch=Branch.TEACHERS)

    letters = teacher_service.get_letters()

    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    keyboard = get_alphabet_keyboard(letters)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_choosing_message("Преподаватели", "Выберите букву фамилии."), keyboard
        )
        reply_markup = None
    else:
        content = LETTER_CHOOSING
        reply_markup = keyboard
    await callback.message.edit_text(
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
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
        telegram_ui_preferences: TelegramUiPreferences = Provide[Deps.telegram_ui_preferences],
):
    """
    Второй уровень навигации преподавателей.
    Ответ - клавиатура с преподавателями на конкретную букву.
    """
    letter = callback_data.letter
    await state.update_data(letter=letter)

    teachers = teacher_service.get_teachers(letter)

    schedule_style = await telegram_ui_preferences.get_schedule_style(callback.from_user.id)
    keyboard = get_teachers_keyboard(teachers)
    if schedule_style == ScheduleStyle.RICH:
        content = add_rich_keyboard(
            get_rich_choosing_message(f"Преподаватели · {letter}", "Выберите преподавателя."),
            keyboard,
        )
        reply_markup = None
    else:
        content = TEACHERS_CHOOSING
        reply_markup = keyboard
    await callback.message.edit_text(
        text=content if isinstance(content, str) else None,
        rich_message=content if isinstance(content, InputRichMessage) else None,
        reply_markup=reply_markup,
    )
    await state.set_state(TeacherStates.choosing_teacher)
    await callback.answer()

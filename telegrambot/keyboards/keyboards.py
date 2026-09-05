from typing import Optional

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from cachetools.func import ttl_cache

from callbacks import (
    EntityCallback,
    FacultyCallback,
    LessonsCallback,
    RichLessonsCallback,
    SubscriptionCallback,
)
from config import settings
from dto import FacultyDTO, GroupDTO, SubscriptionDTO, TeacherDTO, UserDTO
from dto.base_dto import SubscriptableDTO
from enums import EntitySource, ScheduleStyle, SubscriptionAction, ToggleEnum
from . import buttons

ALPHABET_KEYBOARD_ROW_WIDTH = 5
FACULTIES_KEYBOARD_ROW_WIDTH = 3
GROUP_KEYBOARD_ROW_WIDTH = 3


# === Статичные клавиатуры ===
HOME_KB = InlineKeyboardMarkup(inline_keyboard=[[buttons.HOME]])
BACK_HOME_KB = InlineKeyboardMarkup(inline_keyboard=[[buttons.BACK]])
MAIN_BASE_KB = InlineKeyboardMarkup(inline_keyboard=[
    [buttons.GROUPS, buttons.TEACHERS],
    [buttons.SITE]
])
CONFIRM_KB = InlineKeyboardMarkup(inline_keyboard=[[buttons.BACK, buttons.CONFIRM]])


# === Динамические клавиатуры ===
@ttl_cache(maxsize=1000, ttl=180)
def get_main_keyboard(
        subscription_id: Optional[int | str] = None,
        endpoint: Optional[str] = None,
        schedule_style: ScheduleStyle = ScheduleStyle.LEGACY,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if subscription_id:
        for row in buttons.schedule_menu(source=EntitySource.SUBSCRIPTION, style=schedule_style):
            builder.row(*row)
    builder.row(buttons.GROUPS, buttons.TEACHERS)
    builder.row(buttons.USER_SETTINGS)
    if schedule_style == ScheduleStyle.LEGACY:
        builder.row(buttons.get_schedule_ui_toggle(schedule_style))
    if settings.show_entity_links and endpoint:
        builder.row(buttons.get_url_button(endpoint))
    else:
        builder.row(buttons.SITE)
    return builder.as_markup()


def get_settings_keyboard(
        user: UserDTO,
        schedule_style: ScheduleStyle = ScheduleStyle.LEGACY,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        buttons.get_notify_toggle(
            "Изменения в расписании",
            ToggleEnum.CHANGES,
            user.notify_schedule_updates
        )
    )
    builder.row(
        buttons.get_notify_toggle(
            "Напоминания о занятиях",
            ToggleEnum.UPCOMING,
            user.notify_upcoming_lessons
        )
    )
    if user.subscriptions and schedule_style != ScheduleStyle.RICH:
        for sub in user.subscriptions:
            builder.button(
                text=f"✖️ Отписаться от {sub.button_name}",
                callback_data=SubscriptionCallback(
                    action=SubscriptionAction.UNSUBSCRIBE, sub_id=sub.id
                ).pack()
            )
    if schedule_style == ScheduleStyle.RICH:
        builder.row(buttons.get_schedule_ui_toggle(schedule_style))
    builder.adjust(1)
    builder.row(buttons.BACK_HOME, buttons.HOME)
    return builder.as_markup()


@ttl_cache(maxsize=1, ttl=60 * 10)
def get_faculties_keyboard(faculties: tuple[FacultyDTO, ...]) -> InlineKeyboardMarkup:
    """Собирает клавиатуру факультетов из кэша."""
    builder = InlineKeyboardBuilder()
    for faculty in faculties:
        builder.button(
            text=faculty.button_name,
            callback_data=FacultyCallback(faculty_id=faculty.id).pack(),
        )
    if faculties:
        builder.adjust(FACULTIES_KEYBOARD_ROW_WIDTH)  # до 3 факультетов в строке
    builder.row(buttons.BACK_HOME, buttons.HOME)
    return builder.as_markup()


@ttl_cache(maxsize=128, ttl=60 * 10)
def get_grades_keyboard(grades: tuple[int, ...]) -> InlineKeyboardMarkup:
    """Клавиатура курсов для выбранного факультета"""
    builder = InlineKeyboardBuilder()
    for grade in grades:
        builder.add(buttons.get_grade_button(grade))
    builder.row(buttons.BACK, buttons.HOME)
    return builder.as_markup()


@ttl_cache(maxsize=128, ttl=60 * 10)
def get_groups_keyboard(groups: tuple[GroupDTO, ...]) -> InlineKeyboardMarkup:
    """Собирает клавиатуру групп для выбранного факультета и курса."""
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(
            text=group.button_name,
            callback_data=EntityCallback(id=group.id).pack(),
        )
    if groups:
        builder.adjust(GROUP_KEYBOARD_ROW_WIDTH)  # до 2 групп в строке
    builder.row(buttons.BACK, buttons.HOME)
    return builder.as_markup()


@ttl_cache(maxsize=1, ttl=60 * 20)
def get_alphabet_keyboard(letters: tuple[str, ...]) -> InlineKeyboardMarkup:
    """Собирает клавиатуру с буквами алфавита из teachers_cache."""
    builder = InlineKeyboardBuilder()
    for letter in letters:
        builder.add(buttons.get_letter_button(letter))
    if letters:
        builder.adjust(ALPHABET_KEYBOARD_ROW_WIDTH) # букв в одной строке
    builder.row(buttons.BACK_HOME, buttons.HOME)
    return builder.as_markup()


@ttl_cache(maxsize=33, ttl=60 * 10)
def get_teachers_keyboard(teachers: tuple[TeacherDTO, ...]) -> InlineKeyboardMarkup:
    """Собирает клавиатуру учителей для выбранной буквы."""
    builder = InlineKeyboardBuilder()
    for teacher in teachers:
        builder.button(
            text=teacher.button_name,
            callback_data=EntityCallback(id=teacher.id).pack(),
        )
    # TODO: Такое вычисление количества кнопок в строке потенциально опасное
    #  Элементов в teachers в теории может оказаться слишком много.
    row_width = len(teachers) // 10 + 1
    builder.adjust(row_width)
    builder.row(buttons.BACK, buttons.HOME)
    return builder.as_markup()


def get_actions_keyboard(
        obj: SubscriptableDTO,
        subscription: Optional[SubscriptionDTO] = None,
        schedule_style: ScheduleStyle = ScheduleStyle.LEGACY,
) -> InlineKeyboardMarkup:
    """Собирает клавиатуру действий для выбранного объекта (группы или учителя)"""
    builder = InlineKeyboardBuilder()
    for row in buttons.schedule_menu(source=EntitySource.CONTEXT, style=schedule_style):
        builder.row(*row)
    if subscription is not None:
        subscription_button = buttons.unsubscribe(subscription.id)
    else:
        subscription_button = buttons.SUBSCRIBE

    if schedule_style == ScheduleStyle.RICH:
        builder.row(subscription_button)
    else:
        builder.add(subscription_button)
        if settings.show_entity_links and obj.endpoint:
            builder.add(buttons.get_url_button(obj.endpoint))
        builder.adjust(2, 2, 1)

    if schedule_style == ScheduleStyle.RICH and settings.show_entity_links and obj.endpoint:
        builder.row(buttons.get_url_button(obj.endpoint))
    builder.row(buttons.BACK, buttons.HOME)
    return builder.as_markup()


def get_schedule_keyboard(
        callback_data: LessonsCallback | RichLessonsCallback,
        prev_page: int | None,
        next_page: int | None,
) -> InlineKeyboardMarkup:
    """Собирает клавиатуру действий для выбранного объекта (группы или учителя)"""
    builder = InlineKeyboardBuilder()
    source, mode, shift = (
        callback_data.source,
        callback_data.mode,
        callback_data.shift,
    )
    style = (
        ScheduleStyle.RICH
        if isinstance(callback_data, RichLessonsCallback)
        else ScheduleStyle.LEGACY
    )
    if prev_page is not None:
        builder.button(
            text="◀️",
            callback_data=_schedule_callback(style, source, mode, prev_page).pack(),
        )
    builder.button(
        text="🔄 Обновить" if shift == 0 else "🔄 Сегодня",
        callback_data=_schedule_callback(style, source, mode).pack(),
    )
    if next_page is not None:
        builder.button(
            text="▶️",
            callback_data=_schedule_callback(style, source, mode, next_page).pack()
        )
    builder.adjust(3)

    if source == EntitySource.SUBSCRIPTION:
        builder.row(buttons.BACK_HOME)
    else:
        builder.row(buttons.BACK, buttons.HOME)

    return builder.as_markup()


def _schedule_callback(
        style: ScheduleStyle,
        source: str,
        mode: str,
        shift: int = 0,
) -> LessonsCallback | RichLessonsCallback:
    callback_class = RichLessonsCallback if style == ScheduleStyle.RICH else LessonsCallback
    return callback_class(source=source, mode=mode, shift=shift)

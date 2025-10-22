import logging
from datetime import date
from typing import Optional

from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardMarkup,
)
from cachetools.func import ttl_cache

from dto import DateSpanDTO, FacultyDTO, GroupDTO, SubscriptionDTO, TeacherDTO
from dto.subscription_dto import SubscriptableDTO
from enums import EntitySource
from managers.button_manager import Button, EntityCallback, FacultyCallback, LessonsCallback

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 86400  # 24 часа
GROUP_KEYBOARD_ROW_WIDTH = 3
ALPHABET_KEYBOARD_ROW_WIDTH = 5
FACULTIES_KEYBOARD_ROW_WIDTH = 3


class KeyboardManager:
    home = InlineKeyboardMarkup(inline_keyboard=[[Button.home]])
    back_home = InlineKeyboardMarkup(inline_keyboard=[[Button.back, Button.home]])
    main_base = InlineKeyboardMarkup(inline_keyboard=[
        [Button.groups, Button.teachers],
        [Button.site]
    ])

    confirm = InlineKeyboardMarkup(inline_keyboard=[[Button.back, Button.confirm]])

    @classmethod
    @ttl_cache(maxsize=1000, ttl=180)
    def get_main_keyboard(cls, subscription_id: Optional[int | str] = None,
                          endpoint: Optional[str] = None) -> InlineKeyboardMarkup:
        if not subscription_id:
            return cls.main_base  # только базовое меню

        builder = InlineKeyboardBuilder()
        for row in Button.schedule_menu(source=EntitySource.SUBSCRIPTION):
            builder.row(*row)

        builder.row(Button.unsubscribe(subscription_id))
        builder.row(Button.groups, Button.teachers)

        if endpoint is not None:
            builder.row(Button.page_link(endpoint))
        else:
            builder.row(Button.site)

        return builder.as_markup()

    @staticmethod
    @ttl_cache(maxsize=1, ttl=60 * 20)
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
        builder.row(Button.home)
        return builder.as_markup()

    @staticmethod
    @ttl_cache(maxsize=128, ttl=60 * 10)
    def get_grades_keyboard(grades: tuple[int, ...]) -> InlineKeyboardMarkup:
        """
        Клавиатура курсов для выбранного факультета
        """
        builder = InlineKeyboardBuilder()

        for grade in grades:
            builder.add(Button.grade(grade))

        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @staticmethod
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

        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @staticmethod
    @ttl_cache(maxsize=1, ttl=60 * 20)
    def get_alphabet_keyboard(letters: tuple[str, ...]) -> InlineKeyboardMarkup:
        """Собирает клавиатуру с буквами алфавита из teachers_cache."""
        builder = InlineKeyboardBuilder()

        for letter in letters:
            builder.add(Button.letter(letter))

        if letters:
            builder.adjust(ALPHABET_KEYBOARD_ROW_WIDTH)  # 5 букв в строке
        builder.row(Button.home)
        return builder.as_markup()

    @staticmethod
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
        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @classmethod
    def get_actions_keyboard(
            cls,
            obj: SubscriptableDTO,
            subscription: Optional[SubscriptionDTO] = None
    ) -> InlineKeyboardMarkup:
        """Собирает клавиатуру действий для выбранного объекта (группы или учителя)"""
        builder = InlineKeyboardBuilder()
        for row in Button.schedule_menu(source=EntitySource.CONTEXT):
            builder.row(*row)

        if subscription is not None:
            builder.add(Button.unsubscribe(subscription.id))
        else:
            builder.add(Button.subscribe)

        if obj.link is not None:
            builder.add(Button.page_link(obj.link))

        builder.adjust(2, 2, 1)
        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @classmethod
    def get_schedule_keyboard(
            cls,
            callback_data: LessonsCallback,
            date_span: DateSpanDTO,
    ) -> InlineKeyboardMarkup:
        """Собирает клавиатуру действий для выбранного объекта (группы или учителя)"""
        mode, shift, source = callback_data.mode, callback_data.shift, callback_data.source
        today = date.today()

        builder = InlineKeyboardBuilder()

        if (today - date_span.end).days <= 180:
            builder.button(
                text="◀️",
                callback_data=LessonsCallback(source=source, mode=mode, shift=shift - 1).pack(),
            )

        builder.button(
            text="🔄 Обновить" if date_span.start <= today <= date_span.end else "🔄 Сегодня",
            callback_data=LessonsCallback(source=source, mode=mode).pack(),
        )

        if (date_span.end - today).days <= 4:
            builder.button(
                text="▶️",
                callback_data=LessonsCallback(source=source, mode=mode, shift=shift + 1).pack()
            )

        builder.adjust(3)
        builder.row(Button.home)
        return builder.as_markup()

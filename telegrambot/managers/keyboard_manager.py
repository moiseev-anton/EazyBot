import logging
from typing import Dict, Any, List

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from cachetools.func import ttl_cache

from cache import KeyboardDataStore
from config import settings

from dto import UserDTO, SubscriptionDTO, FacultyDTO, GroupDTO, TeacherDTO

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 86400  # 24 часа
KEYBOARD_ROW_WIDTH = 4
TEACHER_KEYBOARD_ROW_WIDTH = 2
GROUP_KEYBOARD_ROW_WIDTH = 2
CHAR_KEYBOARD_ROW_WIDTH = 4
FACULTIES_KEYBOARD_ROW_WIDTH = 1


class FacultyCallback(CallbackData, prefix="f"):
    faculty_id: int


class GradeCallback(CallbackData, prefix="grade"):
    grade: int


class GroupCallback(CallbackData, prefix="g"):
    group_id: int


class AlphabetCallback(CallbackData, prefix="a"):
    letter: str


class TeacherCallback(CallbackData, prefix="t"):
    teacher_id: int


class EntityCallback(CallbackData, prefix="e"):
    id: int


class ActionCallback(CallbackData, prefix="action"):
    action: str
    type: str
    id: int


class Button:
    _emoji_nums = {
        "0": "0️⃣",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣",
        "7": "7️⃣",
        "8": "8️⃣",
        "9": "9️⃣",
    }

    home = InlineKeyboardButton(text="🏠 На главную", callback_data="main")
    phone = InlineKeyboardButton(text="📞 Поделиться номером", request_contact=True)

    today = InlineKeyboardButton(text="Сегодня", callback_data="schedule_today")
    tomorrow = InlineKeyboardButton(text="Завтра", callback_data="schedule_tomorrow")
    ahead = InlineKeyboardButton(text="Предстоящее", callback_data="schedule_ahead")
    week = InlineKeyboardButton(text="Неделя", callback_data="week_schedule")

    groups = InlineKeyboardButton(text="🎓Группы", callback_data="faculties")
    teachers = InlineKeyboardButton(
        text="👨‍🏫👩‍🏫Преподаватели", callback_data="alphabet"
    )
    # notifications = InlineKeyboardButton(
    #     text="🔔Уведомления", callback_data="notifications"
    # )
    site = InlineKeyboardButton(text="🌍Сайт", url=settings.base_link)

    context_schedule = InlineKeyboardButton(
        text="🗓️ Расписание", callback_data="schedule_context"
    )
    subscribe = InlineKeyboardButton(text="📌 Подписаться", callback_data="subscribe")

    back = InlineKeyboardButton(text="◀️ Назад", callback_data="back")

    main_menu = [
        [groups, teachers],
        [site],
    ]

    schedule_menu = [[today, tomorrow], [ahead, week]]

    subscribe_menu = [[subscribe], [home]]

    @classmethod
    def replace_with_emojis(cls, text: str):
        """Заменяет все цифры в строке на эмодзи"""
        return "".join(cls._emoji_nums.get(char, char) for char in text)

    @classmethod
    def grade(cls, digit: int):
        """Создаёт кнопку курса с эмодзи."""
        return InlineKeyboardButton(
            text=f"\t\t{cls.replace_with_emojis(str(digit))}\t\t",
            callback_data=GradeCallback(grade=digit).pack(),
        )

    @classmethod
    def letter(cls, letter: str) -> InlineKeyboardButton:
        """Создаёт кнопку курса с эмодзи."""
        return InlineKeyboardButton(
            text=f"\t\t{letter}\t\t", callback_data=AlphabetCallback(letter=letter).pack()
        )

    @classmethod
    def get_subscription_button(cls, subscription: SubscriptionDTO) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=f"🗓️ {subscription.display_name}", callback_data="subscription")


class KeyboardManager:
    home = InlineKeyboardMarkup(inline_keyboard=[[Button.home]])
    back_home = InlineKeyboardMarkup(inline_keyboard=[[Button.back, Button.home]])
    phone_request = InlineKeyboardMarkup(
        inline_keyboard=[[Button.phone], [Button.home]]
    )
    main_base = InlineKeyboardMarkup(inline_keyboard=Button.main_menu)
    main_with_schedule = InlineKeyboardMarkup(
        inline_keyboard=(Button.schedule_menu + Button.main_menu)
    )
    subscribe = InlineKeyboardMarkup(inline_keyboard=Button.subscribe_menu)
    extend_subscribe = InlineKeyboardMarkup(
        inline_keyboard=[[Button.context_schedule]] + Button.subscribe_menu
    )

    def __init__(self, cache_store: KeyboardDataStore):
        self.cache_store = cache_store

    @classmethod
    def get_main_keyboard(cls, user_dto: UserDTO) -> InlineKeyboardMarkup:
        if user_dto.subscriptions:
            return cls.main_with_schedule
        return cls.main_base

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
            builder.adjust(3)  # до 3 факультетов в строке
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
                callback_data=GroupCallback(group_id=group.id).pack(),
            )

        if groups:
            builder.adjust(2)  # до 2 групп в строке

        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @staticmethod
    @ttl_cache(maxsize=1, ttl=60 * 30)
    def get_alphabet_keyboard(letters: tuple[str, ...]) -> InlineKeyboardMarkup:
        """Собирает клавиатуру с буквами алфавита из teachers_cache."""
        builder = InlineKeyboardBuilder()

        for letter in letters:
            builder.add(Button.letter(letter))

        if letters:
            builder.adjust(5)  # 5 букв в строке
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
                callback_data=TeacherCallback(teacher_id=teacher.id).pack(),
            )

        if teachers:
            if len(teachers) > 10:
                builder.adjust(2)
            else:
                builder.adjust(1)  # 1 учитель в строке
        builder.row(Button.back, Button.home)
        return builder.as_markup()

    @classmethod
    def get_actions_keyboard(cls, obj: GroupDTO | TeacherDTO,) -> InlineKeyboardMarkup:
        """Собирает клавиатуру действий для выбранного объекта (группы или учителя)"""
        builder = InlineKeyboardBuilder()
        obj_type = obj.__class__.__name__
        builder.button(
            text="🗓 Расписание",
            callback_data=ActionCallback(action='schedule', type=obj_type, id=obj.id).pack()
        )
        builder.button(
            text="⭐ Подписаться",
            callback_data=ActionCallback(action='subscribe', type=obj_type, id=obj.id).pack()
        )
        if obj.link is not None:
            builder.button(
                text="🌍 На сайте",
                url=settings.base_link + obj.link
            )

        builder.adjust(1)
        builder.row(Button.back, Button.home)
        return builder.as_markup()

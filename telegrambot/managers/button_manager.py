import logging
from functools import lru_cache
from typing import List, Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardButton

from config import settings
from enums import NavigationAction, ModeEnum, SubscriptionAction
from managers.utills import replace_digits_to_emojis

logger = logging.getLogger(__name__)


class FacultyCallback(CallbackData, prefix="f"):
    faculty_id: int


class GradeCallback(CallbackData, prefix="grade"):
    grade: int


class AlphabetCallback(CallbackData, prefix="a"):
    letter: str


class EntityCallback(CallbackData, prefix="e"):
    id: int


class SubscriptionCallback(CallbackData, prefix="sub"):
    action: str  # subscribe, unsubscribe
    sub_id: Optional[int] = None


class LessonsCallback(CallbackData, prefix="les"):
    source: str  # context, subscription
    mode: str  # today, tomorrow, ahead, week
    shift: int = 0

class ToggleCallback(CallbackData, prefix="toggle"):
    flag_name: str


class Button:

    # === Навигация ===
    home = InlineKeyboardButton(text="🏠 На главную", callback_data=NavigationAction.MAIN)
    back_home = InlineKeyboardButton(text="◀️ Назад", callback_data=NavigationAction.MAIN)
    back = InlineKeyboardButton(text="◀️ Назад", callback_data=NavigationAction.BACK)
    confirm = InlineKeyboardButton(text="Продолжить 🆗", callback_data=NavigationAction.CONFIRM)

    # === Кнопки главного экрана ===
    groups = InlineKeyboardButton(text="🎓Группы", callback_data=NavigationAction.FACULTIES)
    teachers = InlineKeyboardButton(text="👨‍🏫👩‍🏫Преподаватели", callback_data=NavigationAction.ALPHABET)
    site = InlineKeyboardButton(text="🌍Сайт", url=settings.base_link)
    user_settings = InlineKeyboardButton(text="⚙️Настройки", callback_data=NavigationAction.SETTINGS)

    subscribe = InlineKeyboardButton(
        text="⭐ Подписаться",
        callback_data=SubscriptionCallback(action=SubscriptionAction.SUBSCRIBE).pack()
    )

    @staticmethod
    def unsubscribe(sub_id: int | str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text="✖️ Отписаться",
            callback_data=SubscriptionCallback(action=SubscriptionAction.UNSUBSCRIBE, sub_id=sub_id).pack()
        )

    @staticmethod
    @lru_cache(maxsize=None)
    def schedule_menu(source: str) -> List[List[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton(
                    text="🗓 Сегодня",
                    callback_data=LessonsCallback(source=source, mode=ModeEnum.ONE_DAY).pack(),
                ),
                InlineKeyboardButton(
                    text="🗓 Завтра",
                    callback_data=LessonsCallback(source=source, mode=ModeEnum.ONE_DAY, shift=1).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗓 На 3 дня",
                    callback_data=LessonsCallback(source=source, mode=ModeEnum.THREE_DAYS).pack(),
                ),
                InlineKeyboardButton(
                    text="🗓 Неделя",
                    callback_data=LessonsCallback(source=source, mode=ModeEnum.WEEK).pack(),
                ),
            ],
        ]

    @staticmethod
    @lru_cache(maxsize=10)
    def grade(digit: int):
        """Создаёт кнопку курса с эмодзи."""
        return InlineKeyboardButton(
            text=f"\t\t{replace_digits_to_emojis(digit)}\t\t",
            callback_data=GradeCallback(grade=digit).pack(),
        )

    @staticmethod
    @lru_cache(maxsize=36)
    def letter(letter: str) -> InlineKeyboardButton:
        """Создаёт кнопку курса с эмодзи."""
        return InlineKeyboardButton(
            text=f"\t\t{letter}\t\t", callback_data=AlphabetCallback(letter=letter).pack()
        )

    @staticmethod
    def page_link(endpoint: str) -> Optional[InlineKeyboardButton]:
        return InlineKeyboardButton(
            text="🔗 Страница расписания",
            url=settings.base_link + endpoint,
        )

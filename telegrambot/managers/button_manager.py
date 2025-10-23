import logging
from functools import lru_cache
from typing import List, Optional

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardButton

from config import settings
from enums import NavigationAction, ModeEnum, SubscriptionAction

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

    # === Навигация ===
    home = InlineKeyboardButton(text="🏠 На главную", callback_data=NavigationAction.MAIN)
    back = InlineKeyboardButton(text="◀️ Назад", callback_data=NavigationAction.BACK)
    confirm = InlineKeyboardButton(text="Продолжить 🆗", callback_data=NavigationAction.CONFIRM)

    # === Кнопки главного экрана ===
    groups = InlineKeyboardButton(text="🎓Группы", callback_data=NavigationAction.FACULTIES)
    teachers = InlineKeyboardButton(text="👨‍🏫👩‍🏫Преподаватели", callback_data=NavigationAction.ALPHABET)
    site = InlineKeyboardButton(text="🌍Сайт", url=settings.base_link)

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

    @classmethod
    def replace_with_emojis(cls, text: str):
        """Заменяет все цифры в строке на эмодзи"""
        return "".join(cls._emoji_nums.get(char, char) for char in text)

    @classmethod
    @lru_cache(maxsize=10)
    def grade(cls, digit: int):
        """Создаёт кнопку курса с эмодзи."""
        return InlineKeyboardButton(
            text=f"\t\t{cls.replace_with_emojis(str(digit))}\t\t",
            callback_data=GradeCallback(grade=digit).pack(),
        )

    @classmethod
    @lru_cache(maxsize=36)
    def letter(cls, letter: str) -> InlineKeyboardButton:
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

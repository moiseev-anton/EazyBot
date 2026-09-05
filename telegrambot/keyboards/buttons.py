import logging
from functools import lru_cache
from typing import List
from aiogram.utils.keyboard import InlineKeyboardButton
from config import settings
from enums import NavigationAction, ModeEnum, ScheduleStyle, SubscriptionAction
from callbacks import FacultyCallback, GradeCallback, AlphabetCallback, EntityCallback, LessonsCallback, \
    RichLessonsCallback, ScheduleUiCallback, SubscriptionCallback, ToggleCallback  # Изменено: callbacks в keyboards
from common import replace_digits_to_emojis

logger = logging.getLogger(__name__)

# === Статичные кнопки (константы) ===
HOME = InlineKeyboardButton(text="🏠 На главную", callback_data=NavigationAction.MAIN)
BACK_HOME = InlineKeyboardButton(text="◀️ Назад", callback_data=NavigationAction.MAIN)
BACK = InlineKeyboardButton(text="◀️ Назад", callback_data=NavigationAction.BACK)
CONFIRM = InlineKeyboardButton(text="Продолжить 🆗", callback_data=NavigationAction.CONFIRM)

GROUPS = InlineKeyboardButton(text="🎓Группы", callback_data=NavigationAction.FACULTIES)
TEACHERS = InlineKeyboardButton(text="👨‍🏫👩‍🏫Преподаватели", callback_data=NavigationAction.ALPHABET)
SITE = InlineKeyboardButton(text="🌍Сайт", url=settings.base_link)
USER_SETTINGS = InlineKeyboardButton(text="⚙️Настройки", callback_data=NavigationAction.SETTINGS)

SUBSCRIBE = InlineKeyboardButton(
    text="⭐ Подписаться",
    callback_data=SubscriptionCallback(action=SubscriptionAction.SUBSCRIBE).pack()
)


# === Динамические кнопки ===
def unsubscribe(sub_id: int | str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="✖️ Отписаться",
        callback_data=SubscriptionCallback(action=SubscriptionAction.UNSUBSCRIBE, sub_id=sub_id).pack()
    )

def get_notify_toggle(title: str, flag_name: str, enabled: bool) -> InlineKeyboardButton:
    rb = "🔔" if enabled else "🔕"
    return InlineKeyboardButton(
        text=f"{rb} {title}",
        callback_data=ToggleCallback(flag_name=flag_name).pack()
    )


@lru_cache(maxsize=None)
def schedule_menu(source: str, style: ScheduleStyle = ScheduleStyle.LEGACY) -> List[List[InlineKeyboardButton]]:
    if style == ScheduleStyle.RICH:
        return [[
            InlineKeyboardButton(
                text="🗓 Расписание",
                callback_data=RichLessonsCallback(source=source, mode=ModeEnum.WEEK).pack(),
            ),
        ]]

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


def get_schedule_ui_toggle(style: ScheduleStyle) -> InlineKeyboardButton:
    target_style = ScheduleStyle.RICH if style == ScheduleStyle.LEGACY else ScheduleStyle.LEGACY
    text = "✨ Новый UI" if target_style == ScheduleStyle.RICH else "📝 Старый UI"
    return InlineKeyboardButton(
        text=text,
        callback_data=ScheduleUiCallback(style=target_style).pack(),
    )


@lru_cache(maxsize=10)
def get_grade_button(digit: int) -> InlineKeyboardButton:
    """Создаёт кнопку курса с эмодзи."""
    return InlineKeyboardButton(
        text=f"\t\t{replace_digits_to_emojis(digit)}\t\t",
        callback_data=GradeCallback(grade=digit).pack(),
    )


@lru_cache(maxsize=36)
def get_letter_button(letter: str) -> InlineKeyboardButton:
    """Создаёт кнопку буквы алфавита."""
    return InlineKeyboardButton(
        text=f"\t\t{letter}\t\t", callback_data=AlphabetCallback(letter=letter).pack()
    )


def get_url_button(endpoint: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="🔗 Страница расписания",
        url=settings.base_link + endpoint,
    )

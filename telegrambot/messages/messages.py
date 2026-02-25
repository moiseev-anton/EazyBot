from typing import Optional

from .formatters import format_schedule
from dto import DateSpanDTO, FacultyDTO, GroupDTO, LessonDTO, TeacherDTO, UserDTO
from dto.base_dto import SubscriptableDTO


# === Статичные сообщения ===
ALREADY_HAS_SUBSCRIPTION_WARNING = (
    "❗ Вы уже подписаны на другое расписание.\n"
    "Предыдущая подписка будет отменена."
)

ERROR_DEFAULT = "⚠ Упс, что-то пошло не так. Попробуйте вернуться на главную или перезапустить бот."
STATE_DATA_EXPIRED = "😅 Упс, кажется, данные устарели. Давайте начнём сначала!"

FACULTY_CHOOSING = "Выберите факультет:"
LETTER_CHOOSING = "Выберите букву:"
TEACHERS_CHOOSING = "Выберите преподавателя:"


# === Шаблоны ===
_WELCOME_NEW = "Добро пожаловать, {name}!👋\nРегистрация выполнена успешно."
_WELCOME_BACK = "С возвращением, {name}! 👋"

_AUTH_MESSAGES = {
        "authenticated": "✅ Вы успешно авторизовались, теперь можно вернуться обратно ↩",
        "failed": "⚠ Произошла ошибка авторизации, повторите попытку позже.",
    }

_TYPE_LABELS = {GroupDTO: "Группа", TeacherDTO: "Преподаватель"}


# === Динамические сообщения ===
def get_start_message(
        user: UserDTO,
        is_created: bool,
        nonce_status: Optional[str] = None
) -> str:
    """Формирует стартовое сообщение для пользователя."""
    auth_message = _AUTH_MESSAGES.get(nonce_status, "") if nonce_status else ""
    if not is_created and auth_message:
        return auth_message
    name = user.name
    welcome = _WELCOME_NEW.format(name=name) if is_created else _WELCOME_BACK.format(name=name)
    return f"{welcome}\n\n{auth_message}" if auth_message else welcome


def get_main_message(user: UserDTO) -> str:
    lines = [
        f"👤 <b>{f"{user.name}"}</b>",
        f"🪪 <i>{user.username}</i>\n",
        "Расписание:"
    ]
    if user.subscriptions:
        for sub in user.subscriptions:
            lines.append(f"⭐️ <b>{sub.button_name}</b>")
    else:
        lines.append(f"<b>☆ не выбрано</b>")
    return "\n".join(lines)


def get_grade_choosing_msg(faculty: FacultyDTO) -> str:
    """Сообщение для выбора курса с указанием факультета."""
    return (f"{faculty.title}\n"
            "\n"
            "Выберите курс:")


def get_group_choosing_msg(faculty: FacultyDTO, grade: int) -> str:
    """Сообщение для выбора группы с указанием факультета и курса."""
    return (f"{faculty.title}\n"
            f"{grade} курс\n"
            "\n"
            "Выберите группу:")


def get_selected_msg(
        obj: SubscriptableDTO,
        is_subscribed: bool
) -> str:
    label = _TYPE_LABELS.get(type(obj), "Выбрано")
    lines = (
        f"{label}:\n",
        f"<b>{obj.display_name}</b>",
        "\n\n✅ Вы подписаны" if is_subscribed else "",
    )
    return "".join(lines)


def get_schedule_msg(target_obj: SubscriptableDTO, lessons: list[LessonDTO], date_range: DateSpanDTO) -> str:
    """Форматирует сообщение с расписанием для группы или преподавателя"""
    return format_schedule(target_obj, lessons, date_range)


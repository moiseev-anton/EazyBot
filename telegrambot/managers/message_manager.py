import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from jsonapi_client.document import Document

from dto import FacultyDTO, GroupDTO, SubscriptionDTO, TeacherDTO, UserDTO
from dto.base_dto import SubscriptableDTO

logger = logging.getLogger(__name__)


@dataclass
class PeriodDTO:
    lesson_number: int
    date: str
    start_time: str
    end_time: str


@dataclass
class LessonDTO:
    period: PeriodDTO
    group: str
    subgroup: str
    subject: str
    classroom: str
    teacher: TeacherDTO

    def __post_init__(self):
        # Преобразуем строковые данные в объекты Period и Teacher
        if isinstance(self.period, dict):
            self.period = PeriodDTO(**self.period)
        if isinstance(self.teacher, dict):
            self.teacher = TeacherDTO(**self.teacher)

    def format_time(self) -> str:
        """Форматирует время урока"""
        return self.period.start_time[:5]  # HH:MM

    def format_subgroup(self) -> str:
        """Форматирует подгруппу (если есть)"""
        return f"{self.subgroup} подгруппа" if self.subgroup != "0" else None

    def format_for_group(self) -> str:
        """Форматирует урок для отображения в групповом расписании"""
        lines = [
            f"{self._get_emoji()}  <b>{self.format_time()}</b>   📍{self.classroom or '-'}",
            f"<b>{self.subject}</b>",
            self.format_subgroup(),
            f"<i>{self.teacher.short_name}</i>" if self.teacher else None
        ]
        return "\n".join(filter(None, lines))

    def format_for_teacher(self) -> str:
        """Форматирует урок для отображения в преподавательском расписании"""
        lines = [
            f"{self._get_emoji()}  <b>{self.format_time()}</b>   📍{self.classroom or '-'}",
            f"<b>{self.subject}</b>",
            self.format_subgroup(),
            f"<i>{self.group}</i>"
        ]
        return "\n".join(filter(None, lines))

    def _get_emoji(self) -> str:
        """Возвращает эмодзи для номера урока"""
        emoji_map = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
            5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"
        }
        return emoji_map.get(self.period.lesson_number, str(self.period.lesson_number))


class ScheduleMessageBuilder:
    """Класс для построения сообщений с расписанием"""
    EMPTY_SCHEDULE = "📅 Занятий нет"

    _WEEKDAYS_RU = {
        0: "ПОНЕДЕЛЬНИК",
        1: "ВТОРНИК",
        2: "СРЕДА",
        3: "ЧЕТВЕРГ",
        4: "ПЯТНИЦА",
        5: "СУББОТА",
        6: "ВОСКРЕСЕНЬЕ"
    }

    @classmethod
    def _format_date(cls, date_str: str) -> str:
        """Форматирует дату: Понедельник ДД.ММ.ГГГГ"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = cls._WEEKDAYS_RU[date_obj.weekday()]
        date_formatted = date_obj.strftime("%d.%m.%Y")
        return f"<b>{day_name}</b> {date_formatted}"

    @classmethod
    def build_schedule(
            cls,
            title: str,
            lessons_doc: Document,
            for_teacher: bool = False
    ) -> str:
        """Строит сообщение с расписанием"""
        lessons = lessons_doc.resources

        if not lessons:
            return cls.EMPTY_SCHEDULE  # Занятий нет

        # группируем уроки по дате
        grouped = defaultdict(list)
        for lesson in lessons:
            grouped[lesson.date].append(lesson)

        # сортируем даты
        sorted_dates = sorted(grouped.keys())

        message_lines = [f"🗓️ <b>{title}</b>", ""]

        for date_str in sorted_dates:
            message_lines.append(cls._format_date(date_str))

            lessons_for_day = grouped[date_str]

            lessons = [LessonDTO(**lesson_data) for lesson_data in day["lessons"]]
            formatted_lessons = [
                lesson.format_for_teacher() if for_teacher else lesson.format_for_group()
                for lesson in lessons
            ]

            message_lines.append(f"<blockquote>{'\n\n'.join(formatted_lessons)}</blockquote>")
            message_lines.append("")

        # Убираем последнюю пустую строку
        return "\n".join(message_lines[:-1])


class MessageManager:
    # === Регистрация/Авторизация ===
    WELCOME_NEW = "Добро пожаловать, {name}!👋\nРегистрация выполнена успешно."
    WELCOME_BACK = "С возвращением, {name}! 👋"

    AUTH_MESSAGES = {
        "authenticated": "✅ Вы успешно авторизовались, теперь можно вернуться обратно ↩",
        "failed": "⚠ Произошла ошибка авторизации, повторите попытку позже.",
    }

    # === Навигация ===
    FACULTY_CHOOSING = "Выберите факультет:"
    _GRADE_CHOOSING = "{faculty_title}\n\nВыберите курс:"
    _GROUPS_CHOOSING = "{faculty_title}\n{grade} курс\n\nВыберите группу:"

    LETTER_CHOOSING = "Выберите букву:"
    TEACHERS_CHOOSING = "Выберите преподавателя:"

    # === Экран выбранного объекта (группа/преподаватель) ===
    _SELECTED_TEMPLATE = ("{label}:\n"
                          "<b>{display_name}</b>"
                          "{subscribed_note}")

    _TYPE_LABELS = {GroupDTO: "Группа", TeacherDTO: "Преподаватель"}

    _SUBSCRIBED_NOTE = "\n\n✅ Вы подписаны"

    # === ПРЕДУПРЕЖДЕНИЯ ===
    ALREADY_HAS_SUBSCRIPTION_WARNING = (
        "❗ Вы уже подписаны на другое расписание.\n"
        "Предыдущая подписка будет отменена."
    )

    # === OШИБКИ ===
    ERROR_DEFAULT = "⚠ Что-то пошло не так, попробуйте снова."

    @classmethod
    def get_start_message(
            cls,
            user: UserDTO,
            is_created: bool,
            nonce_status: Optional[str] = None
    ) -> str:
        """Формирует стартовое сообщение для пользователя."""

        auth_message = cls.AUTH_MESSAGES.get(nonce_status, "") if nonce_status else ""

        if not is_created and auth_message:
            return auth_message

        name = user.first_name
        welcome = (
            cls.WELCOME_NEW.format(name=name)
            if is_created
            else cls.WELCOME_BACK.format(name=name)
        )

        return f"{welcome}\n\n{auth_message}" if auth_message else welcome

    @staticmethod
    def get_main_message(user: UserDTO) -> str:
        lines = [
            f"👤 <b>{f"{user.first_name} {user.last_name}"}</b>",
            f"🔹 <i>{user.username}</i>\n",
        ]
        if user.subscriptions:
            for sub in user.subscriptions:
                lines.append(f"⭐️ <b>{sub.button_name}</b>")
        else:
            lines.append(f"<b>☆ не выбрано</b>")

        return "\n".join(lines)

    @classmethod
    def get_grade_choosing_msg(cls, faculty: FacultyDTO) -> str:
        """Сообщение для выбора курса с указанием факультета."""
        return cls._GRADE_CHOOSING.format(faculty_title=faculty.title)

    @classmethod
    def get_group_choosing_msg(cls, faculty: FacultyDTO, grade: int) -> str:
        """Сообщение для выбора группы с указанием факультета и курса."""
        return cls._GROUPS_CHOOSING.format(
            faculty_title=faculty.title, grade=grade
        )

    @classmethod
    def get_selected_msg(
            cls,
            obj: SubscriptableDTO,
            subscription: Optional[SubscriptionDTO] = None
    ) -> str:
        label = cls._TYPE_LABELS.get(type(obj), "Выбрано")
        subscribed_note = cls._SUBSCRIBED_NOTE if subscription is not None else ""
        return cls._SELECTED_TEMPLATE.format(
            label=label,
            display_name=obj.display_name,
            subscribed_note=subscribed_note,
        )

    @staticmethod
    def format_group_schedule(group_title: str, schedule_data: Dict[str, Any]) -> str:
        """Форматирует расписание для группы"""
        return ScheduleMessageBuilder.build_schedule(group_title, schedule_data)

    @staticmethod
    def format_teacher_schedule(teacher_name: str, schedule_data: Dict[str, Any]) -> str:
        """Форматирует расписание для преподавателя"""
        return ScheduleMessageBuilder.build_schedule(teacher_name, schedule_data, for_teacher=True)

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from aiogram import html

from jsonapi_client.document import Document
from jsonapi_client.resourceobject import ResourceObject
from dto import UserResponseDTO, UserWithIncludeDTO, FacultyDTO, GroupDTO

from cache import KeyboardDataStore

logger = logging.getLogger(__name__)


@dataclass
class PeriodDTO:
    lesson_number: int
    date: str
    start_time: str
    end_time: str


@dataclass
class TeacherDTO:
    id: int
    full_name: str
    short_name: str


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
            return cls.EMPTY_SCHEDULE # Занятий нет

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
    WELCOME_NEW = "Добро пожаловать, {name}!👋\nРегистрация выполнена успешно."
    WELCOME_BACK = "С возвращением, {name}! 👋"

    AUTH_MESSAGES = {
        "authenticated": "✅ Вы успешно авторизовались, теперь можно вернуться обратно ↩",
        "failed": "⚠ Произошла ошибка авторизации, повторите попытку позже.",
    }

    _FACULTY_CHOOSING = "Выберите факультет:"
    _GRADE_CHOOSING = "{faculty_title}\n\nВыберите курс:"
    _GROUPS_CHOOSING = "{faculty_title}\n{grade} курс\n\nВыберите группу:"
    _SELECTED_GROUP = "Группа: {group_title}"

    _LETTER_CHOOSING = "Выберите букву:"
    _TEACHERS_CHOOSING = "Выберите преподавателя:"
    _SELECTED_TEACHER = "Преподаватель: {teacher_full_name}"

    _ERROR_DEFAULT = "⚠ Что-то пошло не так, попробуйте снова."

    @classmethod
    def get_start_message(cls, user_dto: UserResponseDTO) -> str:
        """Формирует стартовое сообщение для пользователя."""

        auth_message = cls.AUTH_MESSAGES.get(user_dto.nonce_status, "") if user_dto.nonce_status else ""

        if not user_dto.created and auth_message:
            return auth_message

        name = user_dto.first_name or "Anonymous"
        welcome = (
            cls.WELCOME_NEW.format(name=name)
            if user_dto.created
            else cls.WELCOME_BACK.format(name=name)
        )

        return f"{welcome}\n\n{auth_message}" if auth_message else welcome

    @staticmethod
    def get_main_message(user: UserWithIncludeDTO)  -> str:
        lines = [
            f"👤 <b>{html.bold(f"{user.first_name} {user.last_name}")}</b>",
            f"\t\t\t # {user.username}",
        ]
        if user.subscriptions:
            for sub in user.subscriptions:
                lines.append(f"📌 <b>{sub.display_name}</b>")
        else:
            lines.append(f"📌 <i>не выбрано</i>")

        return "\n".join(lines)

    @classmethod
    def get_faculty_choosing_msg(cls) -> str:
        """Сообщение для выбора факультета."""
        return cls._FACULTY_CHOOSING

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
    def get_selected_group_msg(cls, group: GroupDTO) -> str:
        """Сообщение после выбора группы."""
        return cls._SELECTED_GROUP.format(group_title=group.display_name)

    @classmethod
    def get_letter_choosing_msg(cls) -> str:
        return cls._LETTER_CHOOSING

    @classmethod
    def get_teacher_choosing_msg(cls) -> str:
        return cls._TEACHERS_CHOOSING

    @classmethod
    def get_selected_teacher_msg(cls, teacher: TeacherDTO) -> str:
        return cls._SELECTED_TEACHER.format(teacher_full_name=teacher.full_name)

    @classmethod
    def get_error_message(cls) -> str:
        """Возвращает стандартное сообщение об ошибке с клавиатурой 'На главную'."""
        return cls._ERROR_DEFAULT

    @staticmethod
    def format_group_schedule(group_title: str, schedule_data: Dict[str, Any]) -> str:
        """Форматирует расписание для группы"""
        return ScheduleMessageBuilder.build_schedule(group_title, schedule_data)

    @staticmethod
    def format_teacher_schedule(teacher_name: str, schedule_data: Dict[str, Any]) -> str:
        """Форматирует расписание для преподавателя"""
        return ScheduleMessageBuilder.build_schedule(teacher_name, schedule_data, for_teacher=True)

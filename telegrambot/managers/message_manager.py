import logging
from datetime import date, timedelta
from typing import Callable, Optional

from dto import DateSpanDTO, FacultyDTO, GroupDTO, LessonDTO, SubscriptionDTO, TeacherDTO, UserDTO
from dto.base_dto import SubscriptableDTO

logger = logging.getLogger(__name__)


class LessonFormatter:
    """Форматирует отдельный урок в текст"""

    @staticmethod
    def emoji_for_number(number: int) -> str:
        mapping = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
            5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"
        }
        return mapping.get(number, str(number))

    @classmethod
    def format_for_group(cls, lesson: LessonDTO) -> str:
        lines = [
            f"{cls.emoji_for_number(lesson.number)}  <b>{lesson.startTime[:5]}</b>   📍{lesson.classroom or '-'}",
            f"<b>{lesson.subject}</b>",
            (f"{lesson.subgroup} подгруппа" if lesson.subgroup and lesson.subgroup != "0" else None),
            f"<i>{lesson.teacher.short_name}</i>" if lesson.teacher else None,
        ]
        return "\n".join(filter(None, lines))

    @classmethod
    def format_for_teacher(cls, lesson: LessonDTO) -> str:
        lines = [
            f"{cls.emoji_for_number(lesson.number)}  <b>{lesson.startTime[:5]}</b>   📍{lesson.classroom or '-'}",
            f"<b>{lesson.subject}</b>",
            (f"{lesson.subgroup} подгруппа" if lesson.subgroup and lesson.subgroup != "0" else None),
            f"<i>{lesson.group.title}</i>" if lesson.group else None,
        ]
        return "\n".join(filter(None, lines))


class ScheduleMessageBuilder:
    """Формирует полное сообщение с расписанием"""
    _FORMATTERS: dict[type, Callable[[LessonDTO], str]] = {
        GroupDTO: LessonFormatter.format_for_group,
        TeacherDTO: LessonFormatter.format_for_teacher,
    }

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
    def build_schedule(
            cls,
            target_obj: SubscriptableDTO,
            lessons: list[LessonDTO],
            date_range: DateSpanDTO,
    ) -> str:
        """Строит итоговое сообщение с расписанием"""
        formatter = cls._resolve_formatter(target_obj)
        title = getattr(target_obj, "button_name", "Расписание")

        grouped = cls._group_by_date(lessons)

        lines = [f"🗓️ <b>{title}</b>", ""]

        for current_date in cls._iter_dates(date_range):
            lines.append(cls._format_date(current_date))
            day_lessons = grouped.get(current_date.isoformat())
            if not day_lessons:
                lines.append("<i>Занятий нет</i>\n")
                continue

            formatted_lessons = [formatter(lesson) for lesson in sorted(day_lessons, key=lambda l: l.number)]
            lines.append(f"<blockquote>{'\n\n'.join(formatted_lessons)}</blockquote>\n")

        return "\n".join(lines).strip()

    @staticmethod
    def _resolve_formatter(target_obj: SubscriptableDTO) -> Callable[[LessonDTO], str]:
        for cls_type, func in ScheduleMessageBuilder._FORMATTERS.items():
            if isinstance(target_obj, cls_type):
                return func
        raise TypeError(f"No formatter found for type {type(target_obj)}")

    @staticmethod
    def _group_by_date(lessons: list[LessonDTO]) -> dict[str, list[LessonDTO]]:
        grouped = {}
        for lesson in lessons:
            grouped.setdefault(lesson.date, []).append(lesson)
        return grouped

    @classmethod
    def _iter_dates(cls, date_range: DateSpanDTO):
        current = date_range.start
        while current <= date_range.end:
            yield current
            current += timedelta(days=1)

    @classmethod
    def _format_date(cls, day: date) -> str:
        weekday = cls._WEEKDAYS_RU[day.weekday()]
        return f"<b>{weekday}</b> {day.strftime('%d.%m.%Y')}"


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
            "Расписание:"
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
    def format_schedule(target_obj: SubscriptableDTO, lessons: list[LessonDTO], date_range: DateSpanDTO) -> str:
        """Форматирует сообщение с расписанием для группы или преподавателя"""
        return ScheduleMessageBuilder.build_schedule(target_obj, lessons, date_range)

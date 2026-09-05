from datetime import time, timedelta, date as Date

from typing import Optional
from aiogram.types import (
    InputRichBlockDetails,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    InputRichMessage,
    RichBlockTableCell,
    RichTextBold,
    RichTextItalic,
    RichTextMarked,
)
from common import replace_digits_to_emojis

from dto import DateSpanDTO, GroupDTO, LessonDTO, TeacherDTO
from dto.base_dto import SubscriptableDTO
from enums import LessonDisplayMode

_WEEKDAYS_RU = (
        "ПОНЕДЕЛЬНИК", "ВТОРНИК", "СРЕДА", "ЧЕТВЕРГ",
        "ПЯТНИЦА", "СУББОТА", "ВОСКРЕСЕНЬЕ"
    )

_WEEKDAY_ABBREVIATIONS_RU = ("ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС")

def _format_date(day: Date) -> str:
    weekday = _WEEKDAYS_RU[day.weekday()]
    return f"<b>{weekday}</b> {day.strftime('%d.%m.%Y')}"

def format_time(value: Optional[time]) -> str:
    return value.strftime("%H:%M") if value else "--:--"


# === Форматировщик урока ===
def format_lesson(lesson: LessonDTO, mode: LessonDisplayMode = LessonDisplayMode.FULL) -> str:
    number_emoji = replace_digits_to_emojis(lesson.number)
    start = format_time(lesson.startTime)
    end = format_time(lesson.endTime)
    part = f" | {replace_digits_to_emojis(lesson.part)}" if lesson.part else ""

    lines = [
        f"{number_emoji}<b>{part} {start} - {end}</b> 📍{lesson.classroom or '-'}",
        f"<b>{lesson.subject}</b>",
    ]

    if LessonDisplayMode.SHOW_SUBGROUP in mode and lesson.subgroup and lesson.subgroup != "0":
        lines.append(f"{lesson.subgroup} подгруппа")

    if LessonDisplayMode.SHOW_GROUP in mode and lesson.group:
        lines.append(f"<i>{lesson.group.title}</i>")

    if LessonDisplayMode.SHOW_TEACHER in mode and lesson.teacher:
        lines.append(f"<i>{lesson.teacher.short_name}</i>")

    return "\n".join(lines)



# === Форматировщик расписания ===
_FORMATTERS = {
    GroupDTO: lambda l: format_lesson(l, LessonDisplayMode.FOR_GROUP),
    TeacherDTO: lambda l: format_lesson(l, LessonDisplayMode.FOR_TEACHER),
}

_EXPANDABLE_THRESHOLD = 10

def format_schedule(
        target_obj: SubscriptableDTO,
        lessons: list[LessonDTO],
        date_range: DateSpanDTO,
) -> str:
    """Строит итоговое сообщение с расписанием"""
    formatter = _FORMATTERS[type(target_obj)]
    title = getattr(target_obj, "button_name", "Расписание")
    grouped = _group_by_date(lessons)

    lines = [f"🗓️ <b>{title}</b>", ""]

    # Определяем, стоит ли сворачивать блоки уроков: <blockquote expandable> или <blockquote>
    is_expandable = len(lessons) > _EXPANDABLE_THRESHOLD
    blockquote_attr = " expandable" if is_expandable else ""

    for current_date in _iter_dates(date_range):
        lines.append(_format_date(current_date))
        day_lessons = grouped.get(current_date.isoformat())
        if not day_lessons:
            lines.append("<i>Занятий нет</i>\n")
            continue

        formatted_lessons = [formatter(l) for l in sorted(day_lessons, key=lambda l: (l.number, l.part))]
        joined_lessons = "\n\n".join(formatted_lessons)
        lines.append(f"<blockquote{blockquote_attr}>{joined_lessons}</blockquote>\n")

    return "\n".join(lines).strip()


def format_rich_schedule(
        target_obj: SubscriptableDTO,
        lessons: list[LessonDTO],
        date_range: DateSpanDTO,
) -> InputRichMessage:
    """Строит расписание из rich-блоков с отдельной таблицей для каждого дня."""
    title = getattr(target_obj, "button_name", "Расписание")
    grouped = _group_by_date(lessons)
    blocks = [InputRichBlockSectionHeading(text=f"🗓️ {title}", size=2)]

    for current_date in _iter_dates(date_range):
        day_lessons = grouped.get(current_date.isoformat())
        cells = []
        if day_lessons:
            cells.extend(
                [_table_cell(_format_rich_lesson(target_obj, lesson))]
                for lesson in sorted(day_lessons, key=lambda lesson: (lesson.number, lesson.part))
            )
        else:
            cells.append([_table_cell("Занятий нет")])

        blocks.append(
            InputRichBlockDetails(
                summary=_format_rich_day_summary(current_date, len(day_lessons or [])),
                blocks=[
                    InputRichBlockTable(
                        is_bordered=True,
                        is_striped=True,
                        cells=cells,
                    )
                ],
            )
        )

    blocks.append(
        InputRichBlockParagraph(
            text=RichTextItalic(text="Обновите расписание для актуальных данных.")
        )
    )

    return InputRichMessage(blocks=blocks)


def _format_rich_day_summary(day: Date, lesson_count: int) -> list:
    return [
        f"{_WEEKDAY_ABBREVIATIONS_RU[day.weekday()]} · {day.strftime('%d.%m.%Y')} · ",
        RichTextMarked(text=f"\u00a0{lesson_count}\u00a0\u200c"),
    ]


def _format_rich_lesson(
        target_obj: SubscriptableDTO,
        lesson: LessonDTO,
) -> list:
    """Повторяет legacy-представление урока, но с native rich-форматированием."""
    number_emoji = replace_digits_to_emojis(lesson.number)
    start = format_time(lesson.startTime)
    end = format_time(lesson.endTime)
    part = f" | {replace_digits_to_emojis(lesson.part)}" if lesson.part else ""
    text = [
        number_emoji,
        RichTextBold(text=f"{part} {start} - {end}"),
        f" 📍{lesson.classroom or '-'}\n",
        RichTextBold(text=lesson.subject),
    ]

    if lesson.subgroup and lesson.subgroup != "0":
        text.extend(["\n", f"{lesson.subgroup} подгруппа"])
    if isinstance(target_obj, GroupDTO) and lesson.teacher:
        text.extend(["\n", RichTextItalic(text=lesson.teacher.short_name)])
    if isinstance(target_obj, TeacherDTO) and lesson.group:
        text.extend(["\n", RichTextItalic(text=lesson.group.title)])

    return text


def _table_cell(
        text,
        *,
        header: bool = False,
        align: str = "left",
) -> RichBlockTableCell:
    return RichBlockTableCell(
        text=text,
        is_header=header or None,
        align=align,
        valign="middle",
    )


def _iter_dates(date_range: DateSpanDTO):
    current = date_range.start
    while current <= date_range.end:
        yield current
        current += timedelta(days=1)


def _group_by_date(lessons: list[LessonDTO]) -> dict[str, list[LessonDTO]]:
    grouped = {}
    for l in lessons:
        grouped.setdefault(l.date, []).append(l)
    return grouped

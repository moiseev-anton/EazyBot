from typing import Optional

from aiogram.filters.callback_data import CallbackData

__all__ = [
    "AlphabetCallback",
    "EntityCallback",
    "FacultyCallback",
    "GradeCallback",
    "LessonsCallback",
    "RichLessonsCallback",
    "ScheduleUiCallback",
    "SubscriptionCallback",
    "ToggleCallback"
]


class AlphabetCallback(CallbackData, prefix="a"):
    letter: str


class EntityCallback(CallbackData, prefix="e"):
    id: int


class FacultyCallback(CallbackData, prefix="f"):
    faculty_id: int


class GradeCallback(CallbackData, prefix="grade"):
    grade: int


class LessonsCallback(CallbackData, prefix="les"):
    source: str  # context, subscription
    mode: str  # today, tomorrow, ahead, week
    shift: int = 0


class RichLessonsCallback(CallbackData, prefix="rles"):
    source: str  # context, subscription
    mode: str  # today, tomorrow, ahead, week
    shift: int = 0


class ScheduleUiCallback(CallbackData, prefix="sui"):
    style: str


class SubscriptionCallback(CallbackData, prefix="sub"):
    action: str  # subscribe, unsubscribe
    sub_id: Optional[int] = None


class ToggleCallback(CallbackData, prefix="toggle"):
    flag_name: str

from datetime import date, timedelta

from dto import DateSpanDTO
from enums import ModeEnum


class ScheduleMode:
    """Базовый класс для всех режимов расписания."""
    _registry: dict[str, "ScheduleMode"] = {}

    name: str
    days: int
    max_back_shift: int
    max_forward_shift: int

    def __new__(cls, name: str):
        """Возвращает зарегистрированный режим по строке имени."""
        if name in cls._registry:
            return cls._registry[name]
        raise ValueError(f"Unknown schedule mode: {name!r}")

    def __init__(self, *_args, **_kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        """Автоматически регистрирует подклассы."""
        super().__init_subclass__(**kwargs)
        if getattr(cls, "name", None):
            instance = super().__new__(cls)
            ScheduleMode._registry[cls.name] = instance

    def start_func(self, today: date) -> date:
        pass

    def get_span(self, shift: int = 0) -> DateSpanDTO:
        start = self.start_func(date.today()) + timedelta(days=shift * self.days)
        end = start + timedelta(days=self.days - 1)
        return DateSpanDTO(start=start, end=end)

    def get_page_range(self, shift: int) -> tuple[int | None, int | None]:
        prev_page = shift - 1 if shift > -self.max_back_shift else None
        next_page = shift + 1 if shift < self.max_forward_shift else None
        return prev_page, next_page

    def __repr__(self):
        return f"<ScheduleMode {self.name!r}>"


# === ОПРЕДЕЛЕНИЕ РЕЖИМОВ ===

class OneDayMode(ScheduleMode):
    name = ModeEnum.ONE_DAY
    days = 1
    max_back_shift = 180
    max_forward_shift = 6

    def start_func(self, today: date) -> date:
        return today


class ThreeDaysMode(ScheduleMode):
    name = ModeEnum.THREE_DAYS
    days = 3
    max_back_shift = 60
    max_forward_shift = 1

    def start_func(self, today: date) -> date:
        return today


class WeekMode(ScheduleMode):
    name = ModeEnum.WEEK
    days = 7
    max_back_shift = 26
    max_forward_shift = 1

    def start_func(self, today: date) -> date:
        return today - timedelta(days=today.weekday())

from datetime import date, datetime, timedelta
from typing import Union

from pydantic import BaseModel, field_validator, model_validator


class DateRangeDTO(BaseModel):
    date_from: date
    date_to: date

    @field_validator("date_from", "date_to", mode="before")
    @classmethod
    def parse_date(cls, value: Union[str, date]) -> date:
        """Позволяет передавать дату как строку ('YYYY-MM-DD') или объект date."""
        if isinstance(value, date):
            return value
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            raise ValueError(f"Invalid date format: {value}. Expected 'YYYY-MM-DD' or date object.")

    @model_validator(mode="after")
    def validate_range(self):
        """Проверка корректности диапазона: начало не позже конца."""
        if self.date_from > self.date_to:
            raise ValueError("date_from cannot be later than date_to.")
        return self

    @classmethod
    def for_day(cls, day: Union[str, date]) -> "DateRangeDTO":
        """Создаёт диапазон на один день."""
        parsed = cls.parse_date(day)
        return cls(date_from=parsed, date_to=parsed)

    @classmethod
    def for_today(cls) -> "DateRangeDTO":
        """Диапазон на сегодняшний день."""
        today = date.today()
        return cls.for_day(today)

    @classmethod
    def for_tomorrow(cls) -> "DateRangeDTO":
        """Диапазон на завтра."""
        tomorrow = date.today() + timedelta(days=1)
        return cls.for_day(tomorrow)

    @classmethod
    def for_current_week(cls) -> "DateRangeDTO":
        """Диапазон на текущую неделю (Пн–Вс)."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return cls(date_from=start_of_week, date_to=end_of_week)

    @property
    def from_str(self) -> str:
        """Возвращает дату начала диапазона в ISO-формате ('YYYY-MM-DD')."""
        return self.date_from.isoformat()

    @property
    def to_str(self) -> str:
        """Возвращает дату конца диапазона в ISO-формате ('YYYY-MM-DD')."""
        return self.date_to.isoformat()

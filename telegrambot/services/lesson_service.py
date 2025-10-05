import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, Dict, Any

from aiogram.types import User
from jsonapi_client.document import Document

from api_client import AsyncClientSession

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class LessonService:

    def __init__(self, api_client: AsyncClientSession, user: User):
        self.api_client = api_client
        self.user = user

    # Основные методы для конкретного объекта
    async def get_actual_lessons(self, obj_type: str, obj_id: str) -> Document:
        """Получает актуальные уроки (начиная с сегодня)"""
        return await self._make_lessons_request(obj_type, obj_id, DateRange(date_from=date.today()))

    async def get_today_lessons(self, obj_type: str, obj_id: str) -> Document:
        """Получает уроки только на сегодня"""
        today = date.today()
        return await self._make_lessons_request(obj_type, obj_id, DateRange(today, today))

    async def get_tomorrow_lessons(self, obj_type: str, obj_id: str) -> Document:
        """Получает уроки только на завтра"""
        tomorrow = date.today() + timedelta(days=1)
        return await self._make_lessons_request(obj_type, obj_id, DateRange(tomorrow, tomorrow))

    async def get_current_week_lessons(self, obj_type: str, obj_id: str) -> Document:
        """Получает уроки на текущую неделю"""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return await self._make_lessons_request(obj_type, obj_id, DateRange(start_of_week, end_of_week))

    async def get_lessons(
            self,
            obj_type: str,
            obj_id: str,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
    ) -> Document:
        """Основной метод для получения уроков с фильтрацией по датам"""
        return await self._make_lessons_request(obj_type, obj_id, DateRange(date_from, date_to))

    async def _make_lessons_request(
        self,
            obj_type: str,
            obj_id: str,
            date_range: DateRange,
    ) -> Document:
        """
        Внутренний метод для выполнения запроса уроков с фильтрацией по объекту и диапазону дат
        """
        from jsonapi_client import Modifier, Filter

        filters = [Filter(**{obj_type: obj_id})]

        if date_range.date_from:
            filters.append(Filter(date_from=date_range.date_from.isoformat()))
        if date_range.date_to:
            filters.append(Filter(date_to=date_range.date_to.isoformat()))

        modifier = sum(filters, Modifier())

        try:
            return await self.api_client.get("lessons", modifier)
        except Exception:
            logger.exception(
                f"Failed to get lessons for {obj_type}:{obj_id}, Range: {date_range}"
            )
            raise


import logging
from datetime import date
from typing import Union

from dependency_injector.wiring import Provide, inject

from dto import DateRangeDTO, LessonDTO
from dto.base_dto import SubscriptableDTO
from repositories import JsonApiLessonRepository

logger = logging.getLogger(__name__)


class LessonService:

    @inject
    async def _get_lessons(
            self,
            target_obj: SubscriptableDTO,
            date_range: DateRangeDTO,
            lesson_repo: JsonApiLessonRepository = Provide["repositories.lesson"],
            **filters,
    ) -> list[LessonDTO]:
        return await lesson_repo.get_lessons(target_obj, date_range, **filters)

    async def get_lessons_for_range(
            self,
            target_obj: SubscriptableDTO,
            date_from: Union[str, date],
            date_to: Union[str, date],
            **filters,
    ) -> list[LessonDTO]:
        """ Получает уроки за диапазон дней. """
        date_range = DateRangeDTO(date_from=date_from, date_to=date_to)
        return await self._get_lessons(target_obj=target_obj, date_range=date_range, **filters)

    async def get_today_lessons(self, target: SubscriptableDTO, **filters) -> list[LessonDTO]:
        """Получает уроки только на сегодня"""
        return await self._get_lessons(target_obj=target, date_range=DateRangeDTO.for_today(), **filters)

    async def get_tomorrow_lessons(self, target: SubscriptableDTO, **filters) -> list[LessonDTO]:
        """Получает уроки только на завтра"""
        return await self._get_lessons(target_obj=target, date_range=DateRangeDTO.for_tomorrow(), **filters)

    async def get_current_week_lessons(self, target: SubscriptableDTO, **filters) -> list[LessonDTO]:
        """Получает уроки на текущую неделю (с понедельника по воскресенье)"""
        return await self._get_lessons(target_obj=target, date_range=DateRangeDTO.for_current_week(), **filters)

    async def get_lessons_for_date(self, target: SubscriptableDTO, day: str | date, **filters) -> list[LessonDTO]:
        """Получает уроки за конкретную дату"""
        return await self._get_lessons(target_obj=target, date_range=DateRangeDTO.for_day(day), **filters)

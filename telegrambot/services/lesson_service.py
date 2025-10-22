import logging

from dependency_injector.wiring import inject, Provide

from dto import DateSpanDTO, LessonDTO
from dto.base_dto import SubscriptableDTO
from repositories import JsonApiLessonRepository

logger = logging.getLogger(__name__)


class LessonService:

    @inject
    async def get_lessons(
            self,
            target_obj: SubscriptableDTO,
            date_span: DateSpanDTO,
            lesson_repo: JsonApiLessonRepository = Provide["repositories.lesson"],
            **filters,
    ) -> list[LessonDTO]:
        return await lesson_repo.get_lessons(target_obj, date_span, **filters)

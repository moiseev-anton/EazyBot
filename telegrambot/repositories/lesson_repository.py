import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import date, timedelta

from jsonapi_client import Inclusion, Modifier, Filter
from jsonapi_client.document import Document
from jsonapi_client.resourceobject import ResourceObject

from api_client import AsyncClientSession
from dto import GroupDTO, LessonDTO, DateRange
from dto.faculty_dto import FacultyDTO

logger = logging.getLogger(__name__)


class JsonApiLessonRepository:
    resource_name = "lessons"

    resource_to_filter_map = {
        "groups": "group",

    }

    def __init__(self, api_client: AsyncClientSession):
        self.api_client = api_client

    async def get_lesson(self, lesson_id: str) -> LessonDTO:
        document: Document = await self.api_client.get(self.resource_name, lesson_id)
        lesson_res = document.resource
        return LessonDTO.from_jsonapi(lesson_res)

    async def get_lessons(self, obj, date_range: DateRange, **filters):
        filter_key = obj.__config__.filter_key
        allowed = obj.__config__.allowed_filters

        applied_filters = [Filter(**{filter_key: obj.id})]

        if date_range.date_from:
            applied_filters.append(Filter(date_from=date_range.date_from.isoformat()))
        if date_range.date_to:
            applied_filters.append(Filter(date_to=date_range.date_to.isoformat()))

        # Проверка дополнительных фильтров
        for k, v in filters.items():
            if k not in allowed:
                raise ValueError(f"Filter '{k}' not allowed for {obj.__class__.__name__}")
            applied_filters.append(Filter(**{k: v}))

        applied_filters.append(Inclusion('teachers', 'groups'))
        modifier = sum(applied_filters, Modifier())

        document = await self.api_client.get("lessons", modifier)

        if hasattr(document, "included") and document.included:
            grouped: dict[str, dict[str, ResourceObject]] = {}

            for resource in document.included:
                grouped.setdefault(resource.type, {})[resource.id] = resource





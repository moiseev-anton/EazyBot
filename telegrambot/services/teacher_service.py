import logging
from collections import defaultdict
from typing import Optional, List, Dict

from dependency_injector.wiring import inject, Provide

from dto import TeacherDTO
from repositories import JsonApiTeacherRepository

logger = logging.getLogger(__name__)


class TeacherService:
    _teachers: tuple[TeacherDTO, ...] = ()
    _teachers_by_id: Dict[int, TeacherDTO] = {}
    _teachers_by_bucket: dict[str, tuple[TeacherDTO, ...]] = {}

    @inject
    async def refresh(
            self,
            teacher_repo: JsonApiTeacherRepository = Provide["repositories.teacher"]
    ):
        teachers: List[TeacherDTO] = await teacher_repo.get_teachers()

        teachers_by_id = {t.id: t for t in teachers}
        buckets: defaultdict[str, list[TeacherDTO]] = defaultdict(list)

        for t in teachers:
            buckets[t.full_name[0].upper()].append(t)

        self._teachers = tuple(teachers)
        self._teachers_by_id = teachers_by_id
        self._teachers_by_bucket = {
            k: tuple(sorted(v, key=lambda t: t.full_name))
            for k, v in buckets.items()
        }

    def get_teachers(self, letter: Optional[str] = None) -> tuple[TeacherDTO, ...]:
        if letter is None:
            return self._teachers
        return self._teachers_by_bucket.get(letter, ())

    def get_teacher(self, teacher_id: int) -> TeacherDTO | None:
        return self._teachers_by_id.get(teacher_id)

    def get_letters(self) -> tuple[str, ...]:
        """Возвращает список букв-бакетов (в алфавитном порядке)."""
        return tuple(sorted(self._teachers_by_bucket.keys()))

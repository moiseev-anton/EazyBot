import logging
from collections import defaultdict
from typing import List

from dependency_injector.wiring import inject, Provide

from dto import GroupDTO, FacultyDTO
from repositories import JsonApiGroupRepository

logger = logging.getLogger(__name__)


class GroupService:
    _groups_by_id: dict[int, GroupDTO] = {}                                     # group_id → GroupDTO
    _faculties_by_id: dict[int, FacultyDTO] = {}                                # faculty_id → FacultyDTO
    _grades_by_faculty: dict[int, tuple[int, ...]] = {}                         # faculty_id → set  курсов
    _groups_by_faculty_grade: dict[tuple[int, int], tuple[GroupDTO, ...]] = {}  # (faculty, grade) → группы
    _faculties: tuple[FacultyDTO, ...] = ()                                     # кортеж факультетов

    @inject
    async def refresh(
            self,
            group_repo: JsonApiGroupRepository = Provide["repositories.group"]
    ):
        groups: List[GroupDTO] = await group_repo.get_groups_with_faculties()

        groups_by_id = {}
        faculties_by_id = {}
        grades_by_faculty = defaultdict(set)
        groups_by_faculty_grade = defaultdict(list)

        for g in groups:
            groups_by_id[g.id] = g
            faculties_by_id[g.faculty.id] = g.faculty
            grades_by_faculty[g.faculty.id].add(g.grade)
            groups_by_faculty_grade[(g.faculty.id, g.grade)].append(g)

        self._groups_by_id = groups_by_id
        self._faculties_by_id = faculties_by_id
        self._faculties = tuple(sorted(faculties_by_id.values(), key=lambda f: f.short_title))
        self._grades_by_faculty = {fid: tuple(sorted(grades)) for fid, grades in grades_by_faculty.items()}
        self._groups_by_faculty_grade = {key: tuple(grps) for key, grps in groups_by_faculty_grade.items()}

    def get_faculties(self) -> tuple[FacultyDTO, ...]:
        return self._faculties

    def get_faculty(self, faculty_id: int) -> FacultyDTO:
        return self._faculties_by_id.get(faculty_id)

    def get_grades_for_faculty(self, faculty_id: int) -> tuple[int, ...]:
        return self._grades_by_faculty.get(faculty_id, ())

    def get_groups_for_faculty_grade(self, faculty_id: int, grade: int) -> tuple[GroupDTO, ...]:
        return self._groups_by_faculty_grade.get((faculty_id, grade), ())

    def get_group(self, group_id: int) -> GroupDTO | None:
        return self._groups_by_id.get(group_id)

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any, Optional, Dict, Callable, List
from pathlib import Path


from api_client import AsyncClientSession
from cache import KeyboardDataStore
from dto import GroupDTO, TeacherDTO
from repositories import JsonApiGroupRepository, JsonApiTeacherRepository

logger = logging.getLogger(__name__)


class CacheService:
    class DataFetchError(Exception):
        pass

    def __init__(
        self,
        group_repository: JsonApiGroupRepository,
        teacher_repository: JsonApiTeacherRepository,
        cache_store: KeyboardDataStore,
        faculties_cache_file: str,
        teachers_cache_file: str,
    ):
        self.group_repository = group_repository,
        self.teacher_repository = teacher_repository,
        self.cache_repository = cache_store
        self.cache_files = {
            "faculties": Path(faculties_cache_file),
            "teachers": Path(teachers_cache_file),
        }

    @staticmethod
    def _load_from_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """Загружает данные из файла или выбрасывает исключение."""
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    logger.warning(f"Invalid data format in {file_path}, expected dict")
            return None
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load cache from {file_path}: {str(e)}")
            return None

    @staticmethod
    def _save_to_file(file_path: Path, data: dict[str, Any]) -> bool:
        """Атомарно сохраняет данные в файл, возвращает статус успеха"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = file_path.with_suffix('.tmp')

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            temp_file.replace(file_path)
            logger.info(f"Data cached in {file_path}.")
            return True
        except (OSError, TypeError) as e:
            logger.error(f"Failed to save data to {file_path}: {str(e)}")
            return False

    @staticmethod
    async def _build_group_map(groups: List[GroupDTO]) -> Dict[int, Dict]:
        """Формирует словарь групп, распределенных по факультетам и курсам."""
        faculty_map: dict[int, dict] = {}

        for group in groups:
            if group.faculty is None:
                continue

            f = group.faculty
            faculty_entry = faculty_map.setdefault(f.id, {"faculty": f, "courses": defaultdict(dict)})
            faculty_entry["courses"][group.grade][group.id] = group

        return faculty_map

    @staticmethod
    async def _build_teachers_map(teachers: List[TeacherDTO]) -> Dict[str, Dict[int, TeacherDTO]]:
        """Формирует словарь преподавателей, сгруппированных по первой букве фамилии."""
        teachers_map: Dict[str, Dict[int, TeacherDTO]] = defaultdict(dict)

        for teacher in teachers:
            first_letter = teacher.full_name[0].upper()
            teachers_map[first_letter][teacher.id] = teacher

        return dict(teachers_map)

    async def update_faculties(self):
        """Обновляет кеш факультетов."""
        group_list = await self.group_repository.get_groups_with_faculties()
        group_map = self._build_group_map(group_list)
        self.cache_repository.faculties = group_map

    async def update_teachers(self):
        """Обновляет кеш преподавателей."""
        teacher_list = await self.teacher_repository.get_teachers()
        teacher_map = self._build_teachers_map(teacher_list)
        self.cache_repository.teachers = teacher_map

    async def update_all(self) -> bool:
        """Обновляет все кеши параллельно.
        True, если успешно обновлены все, иначе False."""
        results = await asyncio.gather(
            self.update_faculties(),
            self.update_teachers(),
            return_exceptions=True
        )
        return all(isinstance(r, bool) and r for r in results)

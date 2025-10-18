from typing import Optional

from pydantic import BaseModel

from dto.group_dto import GroupDTO
from dto.teacher_dto import TeacherDTO


class LessonDTO(BaseModel):
    id: int
    number: int
    date: str
    startTime: str
    endTime: str
    subject: str
    classroom: str
    subgroup: str
    _group_id: int
    group: Optional[GroupDTO] = None
    _teacher_id: int
    teacher: Optional[TeacherDTO] = None

    class Config:
        frozen = True
        _resource_type = "lessons"

    @property
    def resource_type(self) -> int:
        return self.Config._resource_type

    @classmethod
    def from_jsonapi(
            cls,
            l: "ResourceObject",
            group: Optional[GroupDTO] = None,
            teacher: Optional[TeacherDTO] = None,
    ) -> "LessonDTO":
        return cls(
            id=int(l.id),
            number=l.number,
            date=l.date,
            startTime=l.startTime,
            endTime=l.endTime,
            subject=l.subject,
            classroom=l.classroom,
            subgroup=l.subgroup,
            _group_id=int(l.group._resource_identifier.id),
            group=group,
            _teacher_id=int(l.teacher._resource_identifier.id),
            teacher=teacher,
        )

from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import time
from dto.group_dto import GroupDTO
from dto.teacher_dto import TeacherDTO


class LessonDTO(BaseModel):
    id: int
    number: int
    part: int = 0
    date: str
    startTime: Optional[time]
    endTime: Optional[time]
    subject: str
    classroom: str
    subgroup: str = 0
    _group_id: int
    group: Optional[GroupDTO] = None
    _teacher_id: Optional[int]
    teacher: Optional[TeacherDTO] = None

    class Config:
        frozen = True
        _resource_type = "lessons"

    @property
    def resource_type(self) -> int:
        return self.Config._resource_type

    @field_validator("startTime", "endTime", mode="before")
    def parse_time(cls, value):
        if value is None:
            return None
        return time.fromisoformat(value)

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
            part=l.part,
            date=l.date,
            startTime=l.startTime,
            endTime=l.endTime,
            subject=l.subject,
            classroom=l.classroom,
            subgroup=l.subgroup,
            _group_id=int(l.group._resource_identifier.id),
            group=group,
            _teacher_id=(int(res_id.id) if (res_id := l.teacher._resource_identifier) else None) ,
            teacher=teacher,
        )

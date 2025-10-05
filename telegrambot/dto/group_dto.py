from typing import Optional

from pydantic import BaseModel, PrivateAttr

from dto.faculty_dto import FacultyDTO


class GroupDTO(BaseModel):
    id: int
    title: str
    grade: int
    link: str
    faculty_id: int
    faculty: Optional[FacultyDTO] = None

    class Config:
        frozen = True
        resource_type = "groups"
        filter_key = "group"
        allowed_filters = {"subgroup"}

    @property
    def display_name(self):
        return self.title

    @property
    def button_name(self):
        return self.title or 'n/a'

    @classmethod
    def from_jsonapi(cls, g: "ResourceObject", faculty: Optional[FacultyDTO] = None) -> "GroupDTO":
        return cls(
            id=int(g.id),
            title=g.title,
            link=g.link,
            grade=int(g.grade),
            faculty_id=int(g.faculty._resource_identifier.id),
            faculty=faculty
        )



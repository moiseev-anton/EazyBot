from typing import Optional

from dto.base_dto import SubscriptableDTO


class TeacherDTO(SubscriptableDTO):
    id: int
    full_name: str
    short_name: str
    link: Optional[str] = None

    class Config:
        frozen = True
        resource_name = "teachers"
        filter_key = "teacher"
        allowed_filters = set()

    @property
    def display_name(self):
        return self.full_name

    @property
    def button_name(self):
        return self.short_name

    @classmethod
    def from_jsonapi(cls, t: "ResourceObject") -> "TeacherDTO":
        return cls(
            id=int(t.id),
            full_name=t.full_name,
            short_name=t.short_name,
            link=getattr(t, "link", None),
        )

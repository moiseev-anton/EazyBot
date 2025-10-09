from jsonapi_client.resourceobject import ResourceObject
from pydantic import BaseModel

from dto.group_dto import GroupDTO
from dto.teacher_dto import TeacherDTO
from dto.base_dto import SubscriptableDTO



class SubscriptionDTO(BaseModel):
    id: int
    user_id: str
    object: SubscriptableDTO

    class Config:
        frozen = True

    @property
    def is_group(self) -> bool:
        return isinstance(self.object, GroupDTO)

    @property
    def is_teacher(self) -> bool:
        return isinstance(self.object, TeacherDTO)

    @property
    def display_name(self) -> str:
        return self.object.display_name

    @property
    def button_name(self) -> str:
        return self.object.button_name

    @classmethod
    def from_jsonapi(cls, sub: 'ResourceObject', object: SubscriptableDTO) -> "SubscriptionDTO":
        return cls(
            id=sub.id,
            user_id=sub.user._resource_identifier.id,
            object=object
        )





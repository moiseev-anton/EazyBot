import logging

from jsonapi_client import Inclusion
from jsonapi_client.document import Document
from jsonapi_client.resourceobject import ResourceObject

from context import set_hmac
from dto import GroupDTO, SubscriptionDTO, TeacherDTO, UserDTO
from repositories.base_repository import JsonApiBaseRepository
from repositories.exceptions import ApiError

logger = logging.getLogger(__name__)


class JsonApiUserRepository(JsonApiBaseRepository):
    CONTEXT_USER_URL = "users/me"

    SUBSCRIPTIONS_INCLUSION = ("subscriptions.group", "subscriptions.teacher")
    ACCOUNTS_INCLUSION = ("accounts",)

    async def get_user(self) -> UserDTO:
        try:
            with set_hmac(True):
                document: Document = await self.api_client.get(self.CONTEXT_USER_URL)

            user_resource: ResourceObject = document.resource
            return UserDTO.from_jsonapi(user_resource)
        except Exception as e:
            raise ApiError(f"Failed to register user: {str(e)}")

    async def get_user_with_subscriptions(self) -> UserDTO:
        try:
            with set_hmac(True):
                document: Document = await self.api_client.get(self.CONTEXT_USER_URL,
                                                               Inclusion(*self.SUBSCRIPTIONS_INCLUSION))

                subscriptions = []
                grouped_included = self._separate_included_resources(document)
                if grouped_included:
                    # Важно чтобы fetch методы выполнялись в том же контексте, что и первый запрос
                    teacher_subscriptions_map = grouped_included.get("teacher-subscriptions", {})
                    for sub in teacher_subscriptions_map.values():
                        await sub.teacher.fetch()
                        teacher_dto = TeacherDTO.from_jsonapi(sub.teacher.resource)
                        sub_dto = SubscriptionDTO.from_jsonapi(sub, object=teacher_dto)
                        subscriptions.append(sub_dto)

                    group_subscriptions_map = grouped_included.get("group-subscriptions", {})
                    for sub in group_subscriptions_map.values():
                        await sub.group.fetch()
                        group_dto = GroupDTO.from_jsonapi(sub.group.resource)
                        sub_dto = SubscriptionDTO.from_jsonapi(sub, object=group_dto)
                        subscriptions.append(sub_dto)

            user_resource: ResourceObject = document.resource
            return UserDTO.from_jsonapi(user_resource, subscriptions=subscriptions)

        except Exception as e:
            raise ApiError(f"Failed to register user: {str(e)}")

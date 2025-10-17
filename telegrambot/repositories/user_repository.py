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


    async def get_user(self) -> UserDTO:
        try:
            with set_hmac(True):
                document: Document = await self.api_client.get(self.CONTEXT_USER_URL)

            user_resource: ResourceObject = document.resource
            return UserDTO.from_jsonapi(user_resource)
        except Exception as e:
            raise ApiError(f"Failed to register user: {str(e)}")

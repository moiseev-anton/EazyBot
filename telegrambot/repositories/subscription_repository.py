import logging
from typing import List

from jsonapi_client import Inclusion
from jsonapi_client.document import Document
from jsonapi_client.resourceobject import ResourceObject

from context import set_hmac
from dto import GroupDTO, SubscriptionDTO, TeacherDTO, UserDTO
from repositories.base_repository import JsonApiBaseRepository
from repositories.exceptions import ApiError

logger = logging.getLogger(__name__)


class JsonApiSubscriptionRepository(JsonApiBaseRepository):
    resource_name = "subscriptions"

    related_object_map = {
        "teacher": TeacherDTO,
        "group": GroupDTO,
    }

    async def get_user_subscriptions(self) -> List[SubscriptionDTO]:
        try:
            related_names = tuple(self.related_object_map.keys())

            with set_hmac(True):
                document: Document = await self.api_client.get(
                    self.resource_name,
                    Inclusion(*related_names)
                )

                subscriptions = []
                for sub in document.resources:
                    for rel_name in related_names:
                        rel = getattr(sub, rel_name, None)
                        if rel is not None:
                            await rel.fetch()
                            SchemaDTO = self.related_object_map[rel_name]
                            obj = SchemaDTO.from_jsonapi(rel.resource)
                            sub_dto = SubscriptionDTO.from_jsonapi(sub, obj)
                            subscriptions.append(sub_dto)
                            break

            return subscriptions
        except Exception as e:
            raise ApiError(f"Failed to getting user subscriptions: {str(e)}")

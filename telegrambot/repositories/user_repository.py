import logging
from abc import ABC, abstractmethod
from typing import Set, TypeVar, Callable, Any

from jsonapi_client import Inclusion
from jsonapi_client.document import Document
from jsonapi_client.resourceobject import ResourceObject
from pydantic import BaseModel

from api_client import AsyncClientSession
from context import set_hmac
from dto import RegisterUserDTO, UserResponseDTO, UserInclude, GroupDTO, SubscriptionDTO
from dto import UserWithIncludeDTO, TeacherDTO
from dto.user_dto import AccountDTO
from repositories.base_repository import JsonApiBaseRepository
from repositories.exceptions import ApiError

logger = logging.getLogger(__name__)


class JsonApiUserRepository(JsonApiBaseRepository):
    REGISTER_URL = "/auth/"
    REGISTER_WITH_NONCE_URL = "/auth_with_nonce/"
    USER_BY_CONTEXT_URL = "users/me"

    async def register(self, user_dto: RegisterUserDTO) -> UserResponseDTO:
        try:
            attrs = user_dto.model_dump(exclude_none=True)
            url_suffix = self.REGISTER_WITH_NONCE_URL if user_dto.nonce else self.REGISTER_URL

            user_resource = self.api_client.create(_type="users", **attrs)
            with set_hmac(True):
                await user_resource.commit(custom_url=f'{self.api_client.url_prefix}{url_suffix}')

            user_meta = getattr(user_resource, "meta", {})

            return UserResponseDTO(
                id=user_resource.id,
                social_id=user_dto.social_id,
                platform=user_dto.platform,
                first_name=getattr(user_resource, "firstName", user_dto.first_name),
                last_name=getattr(user_resource, "lastName", user_dto.last_name),
                username=getattr(user_resource, "username", user_dto.extra_data.get("username")),
                extra_data=user_dto.extra_data,
                created=getattr(user_meta, "created", False),
                nonce_status=getattr(user_meta, "nonceStatus"),
            )
        except Exception as e:
            raise ApiError(f"Failed to register user: {str(e)}")

    # async def get_user_by_context(self, include: Set[UserInclude] = None) -> UserWithIncludeDTO:
    #     try:
    #         request_args = {"resource_type": self.USER_BY_CONTEXT_URL}
    #
    #         if include:
    #             request_args["resource_id_or_filter"] = Inclusion(*(item.value for item in include))
    #
    #         with set_hmac(True):
    #             document: Document = await self.api_client.get(**request_args)
    #
    #         user_resource: ResourceObject = document.resource
    #
    #         user_dto = UserWithIncludeDTO(
    #             id=user_resource.id,
    #             first_name=user_resource.first_name,
    #             last_name=user_resource.last_name,
    #             username=user_resource.username,
    #             # subscriptions=[] (default)
    #             # accounts=[] (default)
    #         )
    #
    #         grouped = self._separate_included_resources(document)
    #
    #         if grouped:
    #
    #             subscriptions: list[SubscriptionDTO] = []
    #             if UserInclude.SUBSCRIPTIONS_GROUP in include or UserInclude.SUBSCRIPTIONS_TEACHER in include:
    #                 async def build_subscription(
    #                         sub: ResourceObject,
    #                         related_type: str,
    #                         dto_builder: Callable[[ResourceObject], Any]
    #                 ) -> SubscriptionDTO:
    #                     related_id = getattr(sub, related_type)._resource_identifier.id
    #                     related = grouped.get(f"{related_type}s", {}).get(related_id)
    #                     if related is None:
    #                         await getattr(sub, related_type).fetch()
    #                         related = getattr(sub, related_type).resource
    #                     return SubscriptionDTO(id=sub.id, object=dto_builder(related))
    #
    #                 subscription_builders: dict[str, tuple[str, Callable[[ResourceObject], Any]]] = {
    #                     "group-subscriptions": (
    #                         "group",
    #                         lambda g: GroupDTO.from_jsonapi(g)
    #                     ),
    #                     "teacher-subscriptions": (
    #                         "teacher",
    #                         lambda t: TeacherDTO.from_jsonapi(t)
    #                     ),
    #                 }
    #
    #                 for sub_type, (related_field, dto_builder) in subscription_builders.items():
    #                     for sub in grouped.get(sub_type, {}).values():
    #                         subscriptions.append(await build_subscription(sub, related_field, dto_builder))
    #
    #                 user_dto.subscriptions = subscriptions
    #
    #             if UserInclude.ACCOUNTS in include:
    #                 accounts: list[AccountDTO] = []
    #                 res_name = AccountDTO.Config._resource_name
    #
    #                 for acc in grouped.get(res_name, {}).values():
    #                     accounts.append(AccountDTO.from_jsonapi(acc))
    #                 user_dto.accounts = accounts
    #
    #         return user_dto
    #
    #     except Exception as e:
    #         raise ApiError(f"Failed to register user: {str(e)}")

    async def get_user_by_context(self, include: Set[UserInclude] = None) -> UserWithIncludeDTO:
        try:
            request_args = {"resource_type": self.USER_BY_CONTEXT_URL}

            if include:
                request_args["resource_id_or_filter"] = Inclusion(*(item.value for item in include))

            with set_hmac(True):
                document: Document = await self.api_client.get(**request_args)

            user_resource: ResourceObject = document.resource

            user_dto = UserWithIncludeDTO(
                id=user_resource.id,
                first_name=user_resource.first_name,
                last_name=user_resource.last_name,
                username=user_resource.username,
                # subscriptions=[] (default)
                # accounts=[] (default)
            )

            user_resource.subscriptions


            grouped = self._separate_included_resources(document)

            if grouped:

                subscriptions: list[SubscriptionDTO] = []
                if UserInclude.SUBSCRIPTIONS_GROUP in include or UserInclude.SUBSCRIPTIONS_TEACHER in include:
                    async def build_subscription(
                            sub: ResourceObject,
                            related_type: str,
                            dto_builder: Callable[[ResourceObject], Any]
                    ) -> SubscriptionDTO:
                        related_id = getattr(sub, related_type)._resource_identifier.id
                        related = grouped.get(f"{related_type}s", {}).get(related_id)
                        if related is None:
                            await getattr(sub, related_type).fetch()
                            related = getattr(sub, related_type).resource
                        return SubscriptionDTO(id=sub.id, object=dto_builder(related))

                    subscription_builders: dict[str, tuple[str, Callable[[ResourceObject], Any]]] = {
                        "group-subscriptions": (
                            "group",
                            lambda g: GroupDTO.from_jsonapi(g)
                        ),
                        "teacher-subscriptions": (
                            "teacher",
                            lambda t: TeacherDTO.from_jsonapi(t)
                        ),
                    }

                    for sub_type, (related_field, dto_builder) in subscription_builders.items():
                        for sub in grouped.get(sub_type, {}).values():
                            subscriptions.append(await build_subscription(sub, related_field, dto_builder))

                    user_dto.subscriptions = subscriptions

                if UserInclude.ACCOUNTS in include:
                    accounts: list[AccountDTO] = []
                    res_name = AccountDTO.Config._resource_name

                    for acc in grouped.get(res_name, {}).values():
                        accounts.append(AccountDTO.from_jsonapi(acc))
                    user_dto.accounts = accounts

            return user_dto

        except Exception as e:
            raise ApiError(f"Failed to register user: {str(e)}")


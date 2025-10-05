import logging
from typing import Optional

from dependency_injector.wiring import inject, Provide

from config import settings
from dto import TelegramUserDTO, RegisterUserDTO, UserResponseDTO, UserInclude
from repositories import JsonApiUserRepository

logger = logging.getLogger(__name__)


class UserService:

    @inject
    async def register_user(
            self,
            telegram_user: TelegramUserDTO,
            nonce: Optional[str] = None,
            user_repo: JsonApiUserRepository = Provide["repositories.user"]
    ) -> UserResponseDTO:
        register_dto = RegisterUserDTO(
            social_id=str(telegram_user.telegram_id),
            platform=settings.platform,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            extra_data={
                "username": telegram_user.username,
                "language_code": telegram_user.language_code,
                "is_premium": telegram_user.is_premium,
                "added_to_attachment_menu": telegram_user.added_to_attachment_menu,
            },
            nonce=nonce,
        )
        return await user_repo.register(register_dto)

    @inject
    async def get_user_with_subscriptions(
            self,
            user_repo: JsonApiUserRepository = Provide["repositories.user"]
    ):
        return await user_repo.get_user_by_context(
            include={UserInclude.SUBSCRIPTIONS_GROUP, UserInclude.SUBSCRIPTIONS_TEACHER}
        )

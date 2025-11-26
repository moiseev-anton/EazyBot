import logging

from dependency_injector.wiring import inject, Provide

from dto import AuthDTO, AuthResponseDTO, UserDTO
from repositories import JsonApiAccountRepository, JsonApiSubscriptionRepository, JsonApiUserRepository

logger = logging.getLogger(__name__)


class UserService:

    @inject
    async def auth_user(
            self,
            auth_dto: AuthDTO,
            account_repo: JsonApiAccountRepository = Provide["repositories.account"],
            user_repo: JsonApiUserRepository = Provide["repositories.user"]
    ) -> AuthResponseDTO:
        account = await account_repo.get_or_create(auth_dto)
        account.user = await user_repo.get_user()
        return account

    @inject
    async def get_user_with_subscriptions(
            self,
            user_repo: JsonApiUserRepository = Provide["repositories.user"],
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> UserDTO:
        user = await user_repo.get_user()
        subscriptions = await subscription_repo.get_user_subscriptions()
        user.subscriptions = subscriptions

        return user

    @inject
    async def _toggle_flag(
            self,
            flag_name: str,
            user_repo: JsonApiUserRepository = Provide["repositories.user"],
    ):
        user = await user_repo.get_user()
        if not hasattr(user, flag_name):
            raise ValueError(f"Unknown flag {flag_name}")
        changes = {flag_name: not getattr(user, flag_name)}
        await user_repo.update_user(changes)


    async def toggle_notify_schedule_updates(self):
        return await self._toggle_flag(flag_name="notify_schedule_updates")

    async def toggle_notify_upcoming_lessons(self):
        return await self._toggle_flag(flag_name="notify_upcoming_lessons")



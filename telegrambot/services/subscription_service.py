import logging
from typing import List, Optional

from dependency_injector.wiring import Provide, inject

from dto import SubscriptionDTO
from dto.subscription_dto import SubscriptableDTO
from repositories import JsonApiSubscriptionRepository

logger = logging.getLogger(__name__)


class SubscriptionService:

    @inject
    async def get_user_subscriptions(
            self,
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> List[SubscriptionDTO]:
        return await subscription_repo.get_user_subscriptions()

    @inject
    async def get_subscription_by_target(
            self,
            target_obj: SubscriptableDTO,
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> Optional[SubscriptionDTO]:
        return await subscription_repo.get_subscription_by_target(target_obj)


    # async def is_subscribed(self, target_obj: SubscriptableDTO,) -> bool:
    #     """ Проверяет подписан ли пользователь на конкретный объект """
    #     subscription = await self.get_subscription_by_target(target_obj=target_obj)
    #     return subscription is not None

    @inject
    async def has_any_subscriptions(
            self,
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> bool:
        """Проверяет, есть ли у пользователя хотя бы одна активная подписка."""
        count = await subscription_repo.count_user_subscriptions()
        return count > 0

    @inject
    async def subscribe(
            self,
            target_obj: SubscriptableDTO,
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> SubscriptionDTO:
        """Создает новую подписку пользователя"""
        subscription = await subscription_repo.create(target_obj)
        return subscription

    @inject
    async def unsubscribe(
            self,
            sub_id: int | str,
            subscription_repo: JsonApiSubscriptionRepository = Provide["repositories.subscription"]
    ) -> None:
        """Создает новую подписку пользователя"""
        await subscription_repo.delete(sub_id)




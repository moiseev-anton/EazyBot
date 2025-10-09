import logging
from typing import List

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

    async def is_subscribed(self, obj: SubscriptableDTO) -> bool:
        subscriptions = await self.get_user_subscriptions()
        for sub in subscriptions:
            related_obj = sub.object
            if object and related_obj.__class__ == obj.__class__ and related_obj.id == obj.id:
                return True
        return False

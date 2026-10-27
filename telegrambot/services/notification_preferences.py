from dependency_injector.wiring import Provide, inject

from config import settings
from repositories.exceptions import ApiError


NOTIFICATION_TYPES = ("schedule_updated", "lesson_upcoming")


class NotificationPreferences:
    @inject
    async def get_preferences(
            self, social_id: str,
            account_repo=Provide["repositories.account"],
            preference_repo=Provide["repositories.notification_preference"],
    ):
        account_id = await account_repo.get_current_account_id(settings.platform, str(social_id))
        preferences = {}
        for preference in await preference_repo.get_preferences():
            if preference.social_account_id != account_id:
                continue
            if preference.channel != settings.platform:
                raise ApiError("Notification preference platform mismatch")
            if preference.notification_type not in NOTIFICATION_TYPES:
                continue
            if preference.notification_type in preferences:
                raise ApiError("Duplicate notification preference for current account")
            preferences[preference.notification_type] = preference
        if set(preferences) != set(NOTIFICATION_TYPES):
            raise ApiError("Notification preferences for current account are missing")
        return preferences

    @inject
    async def set_enabled(
            self, social_id: str, notification_type: str, enabled: bool, version: str,
            storage=Provide["storage"],
            preference_repo=Provide["repositories.notification_preference"],
    ):
        if notification_type not in NOTIFICATION_TYPES or type(enabled) is not bool:
            raise ValueError("Invalid notification preference change")
        # Serialize changes across different settings messages for this account.
        async with storage.redis.lock(
            f"telegrambot:notification-lock:{settings.platform}:{social_id}",
            timeout=60, blocking_timeout=0,
        ):
            preferences = await self.get_preferences(social_id)
            current = preferences[notification_type]
            if current.version != version or current.enabled == enabled:
                return preferences  # Stale/repeated callback: refresh without changing anything.
            confirmed = await preference_repo.set_enabled(current.id, enabled)
            if (confirmed.id != current.id
                    or confirmed.social_account_id != current.social_account_id
                    or confirmed.channel != settings.platform
                    or confirmed.notification_type != notification_type
                    or confirmed.enabled != enabled):
                raise ApiError("Notification preference change was not confirmed")
            preferences[notification_type] = confirmed
            return preferences

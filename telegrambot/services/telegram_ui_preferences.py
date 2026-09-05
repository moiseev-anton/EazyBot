import logging

from aiogram.fsm.storage.redis import RedisStorage
from redis.exceptions import RedisError

from enums import ScheduleStyle

logger = logging.getLogger(__name__)


class TelegramUiPreferences:
    """Временные UI-предпочтения, привязанные к Telegram ID, а не к пользователю системы."""

    KEY_PREFIX = "telegrambot:preferences:schedule-ui"

    def __init__(self, storage: RedisStorage, ttl: int):
        self.redis = storage.redis
        self.ttl = ttl

    def _schedule_style_key(self, telegram_user_id: int) -> str:
        return f"{self.KEY_PREFIX}:{telegram_user_id}"

    async def get_schedule_style(self, telegram_user_id: int) -> ScheduleStyle:
        value = await self.redis.get(self._schedule_style_key(telegram_user_id))
        if isinstance(value, bytes):
            value = value.decode()

        return ScheduleStyle.RICH if value == ScheduleStyle.RICH else ScheduleStyle.LEGACY

    async def set_schedule_style(
            self,
            telegram_user_id: int,
            style: ScheduleStyle,
    ) -> None:
        key = self._schedule_style_key(telegram_user_id)
        if style == ScheduleStyle.LEGACY:
            await self.redis.delete(key)
            return

        await self.redis.set(key, style.value, ex=self.ttl)

    async def touch_schedule_style(self, telegram_user_id: int) -> None:
        """Продлевает настройку активного пользователя, не создавая её при отсутствии."""
        try:
            await self.redis.expire(self._schedule_style_key(telegram_user_id), self.ttl)
        except RedisError:
            logger.warning("Failed to extend Telegram UI preference TTL", exc_info=True)

import logging

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
from uuid import uuid4
from context import request_context

from dependencies import Deps
from services import TelegramUiPreferences


logger = logging.getLogger(__name__)


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, container: Deps):
        super().__init__()
        self.container = container

    async def __call__(self, handler, event, data):
        # Передаём весь контейнер
        data["deps"] = self.container
        return await handler(event, data)


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, telegram_ui_preferences: TelegramUiPreferences):
        super().__init__()
        self.telegram_ui_preferences = telegram_ui_preferences

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = getattr(event, "from_user", None)

        if user:
            # Ставим контекст пользователя
            request_context.set({
                "user_id": str(user.id),
                "hmac": False,
            })
            await self.telegram_ui_preferences.touch_schedule_style(user.id)

        return await handler(event, data)


class CallbackLockMiddleware(BaseMiddleware):
    """Не допускает одновременную обработку callback-кнопок одного сообщения."""

    LOCK_TTL_SECONDS = 30
    DEFERRED_ANSWER_CALLBACK_PREFIXES = ("les:", "rles:", "sub:")
    RELEASE_LOCK_SCRIPT = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        end
        return 0
    """

    def __init__(self, storage: RedisStorage):
        super().__init__()
        self.redis = storage.redis
        self.release_lock = self.redis.register_script(self.RELEASE_LOCK_SCRIPT)

    async def _acknowledge(self, event: CallbackQuery, text: str | None = None) -> bool:
        try:
            await event.answer(text)
            return True
        except TelegramBadRequest as error:
            if "query is too old" not in str(error).lower():
                raise
            logger.info("Callback query %s has already expired", event.id)
            return False
        except TelegramNetworkError:
            logger.warning("Could not acknowledge callback query %s", event.id)
            return True

    @classmethod
    def _requires_late_answer(cls, event: CallbackQuery) -> bool:
        return (
            event.data == "confirm"
            or bool(event.data and event.data.startswith(cls.DEFERRED_ANSWER_CALLBACK_PREFIXES))
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery) or event.message is None:
            return await handler(event, data)

        lock_key = (
            f"telegrambot:callback-lock:{event.message.chat.id}:{event.message.message_id}"
        )
        lock_token = str(uuid4())
        acquired = await self.redis.set(
            lock_key,
            lock_token,
            nx=True,
            ex=self.LOCK_TTL_SECONDS,
        )

        if not acquired:
            await self._acknowledge(event, "⏳ Запрос уже обрабатывается")
            return None

        if not self._requires_late_answer(event) and not await self._acknowledge(event):
            await self.release_lock(keys=[lock_key], args=[lock_token])
            return None

        try:
            return await handler(event, data)
        finally:
            await self.release_lock(keys=[lock_key], args=[lock_token])

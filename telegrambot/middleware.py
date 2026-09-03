from aiogram import BaseMiddleware
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable
from uuid import uuid4
from context import request_context

from dependencies import Deps


class DependencyMiddleware(BaseMiddleware):
    def __init__(self, container: Deps):
        super().__init__()
        self.container = container

    async def __call__(self, handler, event, data):
        # Передаём весь контейнер
        data["deps"] = self.container
        return await handler(event, data)


class UserContextMiddleware(BaseMiddleware):
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

        return await handler(event, data)


class CallbackLockMiddleware(BaseMiddleware):
    """Не допускает одновременную обработку callback-кнопок одного сообщения."""

    LOCK_TTL_SECONDS = 30
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
            await event.answer("⏳ Запрос уже обрабатывается")
            return None

        try:
            return await handler(event, data)
        finally:
            await self.release_lock(keys=[lock_key], args=[lock_token])

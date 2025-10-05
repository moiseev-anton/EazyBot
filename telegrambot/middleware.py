from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
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

# @formatter:off
#  Monkey-патч для jsonapi_client
from aiogram.types import BotCommand, BotCommandScopeDefault
from api_client.client_patch import patch_jsonapi_client
patch_jsonapi_client(verbose=True)

# @formatter:on
import asyncio
import logging
import sys

from config import settings
from dependencies import Deps
from handlers import (
    entity_router,
    error_router,
    start_router,
    main_router,
    faculty_router,
    teacher_router,
    navigation_router,
    subscription_router,
    lessons_router
)
from middleware import UserContextMiddleware
from tasks import setup_periodic_task_scheduler

from aiogram import Bot, Dispatcher

logging.basicConfig(level=getattr(logging, settings.log_level), stream=sys.stdout)
logger = logging.getLogger(__name__)


async def on_startup(deps: Deps, bot: Bot):
    deps.api_client()                               # Создаем API-client
    await deps.services.teacher().refresh()         # Первичное получение учителей для клавиатур
    await deps.services.group().refresh()           # Первичное получение групп для клавиатур
    await setup_periodic_task_scheduler(deps=deps)  # Запуск планировщика

    # Добавление Меню команд
    commands = [BotCommand(command="start", description="🚀 Перезапуск бота")]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot started.")


async def on_shutdown(deps: Deps):
    api_client = deps.api_client()
    await api_client.close()
    logger.info("Bot stopped.")


async def main():
    container = Deps()
    container.config.from_pydantic(settings)

    bot = container.bot()
    storage = container.storage()
    dp = Dispatcher(bot=bot, storage=storage, deps=container)
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())

    dp.include_routers(
        entity_router,
        faculty_router,
        main_router,
        navigation_router,
        start_router,
        subscription_router,
        teacher_router,
        lessons_router,
        error_router,
    )
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

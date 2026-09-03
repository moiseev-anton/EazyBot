# @formatter:off
#  Monkey-патч для jsonapi_client
from aiogram.types import BotCommand, BotCommandScopeDefault
from api_client.client_patch import patch_jsonapi_client
patch_jsonapi_client(verbose=True)

# @formatter:on
import asyncio
import logging
import sys

from aiohttp import web
from config import settings
from dependencies import Deps
from handlers import *
from middleware import CallbackLockMiddleware, UserContextMiddleware
from tasks import setup_periodic_task_scheduler

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from typing import Literal

bot_mode: Literal["polling", "webhook"]

logging.basicConfig(level=getattr(logging, settings.log_level), stream=sys.stdout)
logger = logging.getLogger(__name__)


async def on_startup(deps: Deps, bot: Bot):
    deps.api_client()                               # Создаем API-client
    await deps.services.teacher().refresh()         # Первичное получение учителей для клавиатур
    await deps.services.group().refresh()           # Первичное получение групп для клавиатур
    await setup_periodic_task_scheduler(deps=deps)  # Запуск планировщика

    # Добавление Меню команд
    commands = [
        BotCommand(command="start", description="🚀 Перезапуск бота"),
        BotCommand(command="main", description="🏠 На главную"),
                ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Bot started.")


async def webhook_startup(bot: Bot):  # ← отдельный async хук только для webhook
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=getattr(settings, 'webhook_secret', None),
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )
    logger.info(f"Webhook установлен: {settings.webhook_url}")


async def on_shutdown(deps: Deps):
    api_client = deps.api_client()
    await api_client.close()
    logger.info("Bot stopped.")


def main():
    container = Deps()
    container.config.from_pydantic(settings)

    bot = container.bot()
    storage = container.storage()
    dp = Dispatcher(bot=bot, storage=storage, deps=container)
    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())
    dp.callback_query.middleware(CallbackLockMiddleware(storage))

    dp.include_routers(
        entity_router,
        faculty_router,
        main_router,
        navigation_router,
        start_router,
        settings_router,
        subscription_router,
        teacher_router,
        lessons_router,
        error_router,
    )
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)


    if settings.bot_mode.lower() == "webhook":
        logger.info("Запуск в режиме WEBHOOK")
        dp.startup.register(webhook_startup)

        # Запускаем aiohttp сервер
        app = web.Application()

        webhook_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=getattr(settings, 'webhook_secret', None),
        )

        webhook_handler.register(app, path=settings.webhook_path)
        setup_application(app, dp, bot=bot)

        # Запуск сервера
        web.run_app(
            app,
            host="0.0.0.0",
            port=settings.webhook_port,
        )

    else:
        logger.info("Запуск в режиме POLLING")

        async def polling_main():
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(
                bot,
                allowed_updates=["message", "callback_query"],
            )

        asyncio.run(polling_main())


if __name__ == "__main__":
    main()

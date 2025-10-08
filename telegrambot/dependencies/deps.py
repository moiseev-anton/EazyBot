from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dependency_injector import containers, providers

from api_client import AsyncClientSession, models_as_jsonschema
from dependencies.repositories import Repositories
from dependencies.services import Services


class Deps(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=[
            "services",
            "handlers",
        ],
    )

    config = providers.Configuration()

    api_client = providers.Singleton(
        AsyncClientSession,
        server_url=config.api_base_url,
        hmac_secret=config.hmac_secret,
        platform=config.platform,
        schema=models_as_jsonschema
    )

    bot = providers.Singleton(
        Bot,
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Redis хранилище (применяется для FSM)
    storage = providers.Singleton(
        RedisStorage.from_url,
        url=config.redis_storage_url,
        state_ttl=config.storage_state_ttl,
        data_ttl=config.storage_data_ttl,
    )

    # Планировщик периодических задач
    scheduler = providers.Singleton(AsyncIOScheduler)

    repositories = providers.Container(
        Repositories,
        config=config,
        api_client=api_client
    )

    services = providers.Container(Services)

from dependency_injector import containers, providers

from api_client import AsyncClientSession
from repositories import (JsonApiAccountRepository, JsonApiGroupRepository, JsonApiLessonRepository,
                          JsonApiSubscriptionRepository, JsonApiTeacherRepository, JsonApiUserRepository)


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    api_client = providers.Dependency(instance_of=AsyncClientSession)

    account = providers.Singleton(JsonApiAccountRepository, api_client=api_client)
    user = providers.Singleton(JsonApiUserRepository, api_client=api_client)
    group = providers.Singleton(
        JsonApiGroupRepository,
        api_client=api_client,
        cache_file_path=config.groups_cache_file_path
    )
    teacher = providers.Singleton(
        JsonApiTeacherRepository,
        api_client=api_client,
        cache_file_path=config.teachers_cache_file_path
    )
    subscription = providers.Singleton(JsonApiSubscriptionRepository, api_client=api_client)
    lesson = providers.Singleton(JsonApiLessonRepository, api_client=api_client)

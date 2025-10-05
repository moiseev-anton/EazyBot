from dependency_injector import containers, providers

from api_client import AsyncClientSession
from repositories import JsonApiUserRepository, JsonApiGroupRepository, JsonApiTeacherRepository


class Repositories(containers.DeclarativeContainer):
    config = providers.Configuration()
    api_client = providers.Dependency(instance_of=AsyncClientSession)

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

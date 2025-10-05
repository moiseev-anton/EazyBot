from dependency_injector import containers, providers

from services import UserService, TeacherService, GroupService, LessonService


class Services(containers.DeclarativeContainer):
    user = providers.Factory(UserService)
    teacher = providers.Singleton(TeacherService)
    group = providers.Singleton(GroupService)
    # lesson = providers.Factory(LessonService)

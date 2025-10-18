from dependency_injector import containers, providers

from services import GroupService, LessonService, SubscriptionService, TeacherService, UserService


class Services(containers.DeclarativeContainer):
    user = providers.Factory(UserService)
    teacher = providers.Singleton(TeacherService)
    group = providers.Singleton(GroupService)
    subscription = providers.Factory(SubscriptionService)
    lesson = providers.Factory(LessonService)

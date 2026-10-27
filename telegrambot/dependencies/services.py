from dependency_injector import containers, providers
from services.notification_preferences import NotificationPreferences

from services import GroupService, LessonService, SubscriptionService, TeacherService, UserService


class Services(containers.DeclarativeContainer):
    user = providers.Factory(UserService)
    notification_preferences = providers.Factory(NotificationPreferences)
    teacher = providers.Singleton(TeacherService)
    group = providers.Singleton(GroupService)
    subscription = providers.Factory(SubscriptionService)
    lesson = providers.Factory(LessonService)

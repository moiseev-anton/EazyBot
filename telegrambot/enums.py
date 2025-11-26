from enum import StrEnum


class EntitySource(StrEnum):
    SUBSCRIPTION = "subscription"
    CONTEXT = "context"


class SubscriptionAction(StrEnum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


class NavigationAction(StrEnum):
    MAIN = "main"  # Главное меню
    BACK = "back"  # Назад
    DELETE = "delete"
    FORWARD = "forward"
    CONFIRM = "confirm"  # Подтвердить действие
    FACULTIES = "faculties"  # Список факультетов
    ALPHABET = "alphabet"  # Выбор по алфавиту
    SETTINGS = "settings"


class Branch(StrEnum):
    GROUPS = "groups"
    TEACHERS = "teachers"


class ModeEnum(StrEnum):
    ONE_DAY = "1day"
    THREE_DAYS = "3days"
    WEEK = "week"

class ToggleEnum(StrEnum):
    UPCOMING = "upcoming"
    CHANGES = "changes"

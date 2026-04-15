from enum import auto, Flag, StrEnum


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


class LessonDisplayMode(Flag):
    SHOW_GROUP = auto()
    SHOW_TEACHER = auto()
    SHOW_SUBGROUP = auto()

    # Предустановленные режимы
    FOR_GROUP = SHOW_TEACHER | SHOW_SUBGROUP
    FOR_TEACHER = SHOW_GROUP | SHOW_SUBGROUP
    FULL = SHOW_GROUP | SHOW_TEACHER | SHOW_SUBGROUP

from pydantic import BaseModel


class SubscriptableDTO(BaseModel):
    """Базовый класс для объектов, на которые можно подписываться."""
    pass

    @property
    def button_name(self) -> str:
        raise NotImplementedError

    @property
    def display_name(self) -> str:
        raise NotImplementedError
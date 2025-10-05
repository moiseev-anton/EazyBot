from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, field_validator, PrivateAttr

from dto.subscription_dto import SubscriptionDTO


class UserInclude(str, Enum):
    SUBSCRIPTIONS = "subscriptions"
    SUBSCRIPTIONS_GROUP = "subscriptions.group"
    SUBSCRIPTIONS_TEACHER = "subscriptions.teacher"
    ACCOUNTS = "accounts"


class TelegramUserDTO(BaseModel):
    telegram_id: int
    first_name: Optional[str] = ""
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = False
    added_to_attachment_menu: Optional[bool] = False

    class Config:
        frozen = True


class RegisterUserDTO(BaseModel):
    social_id: str
    platform: str
    first_name: str
    last_name: Optional[str] = None
    extra_data: Dict[str, Any] = {}
    nonce: Optional[str] = None

    @field_validator("social_id")
    def validate_social_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("social_id cannot be empty")
        return value

    class Config:
        frozen = True


class UserResponseDTO(BaseModel):
    id: str
    social_id: str
    platform: str
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    extra_data: Dict[str, Any] = {}
    created: bool
    nonce_status: Optional[str] = None

    @field_validator("id", "social_id")
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{value.__name__} cannot be empty")
        return value

    class Config:
        frozen = True
        arbitrary_types_allowed = True
        resource_name = "users"


class AccountDTO(BaseModel):
    id: int
    platform: str
    social_id: str
    extra_data: Dict[str, Any] = {}

    class Config:
        frozen = True
        _resource_name = "social-accounts"

    @field_validator("id", "social_id", "platform")
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{value.__name__} cannot be empty")
        return value

    @classmethod
    def from_jsonapi(cls, acc: "ResourceObject") -> "AccountDTO":
        return cls(
            id=int(acc.id),
            platform=acc.title,
            social_id=acc.short_title,
            extra_data=acc.extra_data
        )


class UserWithIncludeDTO(BaseModel):
    id: str
    _resource_type: str = PrivateAttr(default="users")
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    subscriptions: List[SubscriptionDTO] = []
    accounts: List[AccountDTO] = []

    @field_validator("id", "username")
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{value.__name__} cannot be empty")
        return value

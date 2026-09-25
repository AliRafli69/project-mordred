from functools import cached_property

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_allowed_user_ids(value: str) -> frozenset[int]:
    """Parse a comma-separated allowlist of positive Telegram user IDs."""

    entries = [entry.strip() for entry in value.split(",")]

    if not entries or any(not entry for entry in entries):
        raise ValueError("Telegram allowed user IDs must not contain empty entries")

    try:
        user_ids = frozenset(int(entry) for entry in entries)
    except ValueError as exc:
        raise ValueError("Telegram allowed user IDs must be integers") from exc

    if any(user_id <= 0 for user_id in user_ids):
        raise ValueError("Telegram allowed user IDs must be positive")

    return user_ids


class TelegramSettings(BaseSettings):
    """Validated configuration for the Telegram adapter service."""

    model_config = SettingsConfigDict(
        env_prefix="MORDRED_TELEGRAM_",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: SecretStr
    allowed_user_ids: str = Field(min_length=1)

    backend_base_url: AnyHttpUrl = "http://backend:8000"
    backend_api_key: SecretStr

    connect_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    read_timeout_seconds: float = Field(default=100.0, gt=0, le=600)
    poll_timeout_seconds: int = Field(default=30, ge=1, le=50)

    @cached_property
    def allowed_user_id_set(self) -> frozenset[int]:
        return parse_allowed_user_ids(self.allowed_user_ids)

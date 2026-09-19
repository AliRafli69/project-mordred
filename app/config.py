from functools import lru_cache

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated configuration supplied through environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="MORDRED_",
        case_sensitive=False,
        extra="ignore",
    )

    bind_address: str = "127.0.0.1"
    bind_port: int = Field(default=8000, ge=1, le=65535)

    lm_studio_base_url: AnyHttpUrl
    lm_studio_api_key: SecretStr
    lm_studio_model: str = Field(min_length=1)

    chat_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    chat_max_output_tokens: int = Field(default=1024, ge=64, le=4096)

    connect_timeout_seconds: float = Field(default=3.0, gt=0, le=30)
    read_timeout_seconds: float = Field(default=90.0, gt=0, le=600)

    backend_api_key: SecretStr


@lru_cache
def get_settings() -> Settings:
    """Load and cache validated process configuration."""

    return Settings()

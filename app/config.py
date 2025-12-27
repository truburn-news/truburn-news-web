from functools import lru_cache
import os
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    app_env: str = Field("local", env="APP_ENV")
    review_request_duration_hours: int = Field(72, env="REVIEW_REQUEST_DURATION_HOURS")
    base_url: AnyHttpUrl | None = None
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # allow extra env vars like POSTGRES_USER/PASSWORD without failing
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

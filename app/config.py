from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://orders:orders@localhost:5432/orders"
    log_level: str = "INFO"
    page_size_max: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()

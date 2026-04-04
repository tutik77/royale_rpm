from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    player_service_url: str = "http://player-service:8001"
    deck_collector_url: str = "http://collector:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()

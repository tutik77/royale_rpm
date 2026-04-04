from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://deck_collector:deck_collector@db:5432/deck_collector"
    redis_url: str = "redis://redis:6379/0"

    clash_api_base_url: str = "https://api.clashroyale.com/v1"
    clash_api_token: str = ""

    collection_interval_seconds: int = 14400
    top_players_limit: int = 200
    location_id: str = "global"
    request_delay: float = 0.05


@lru_cache
def get_settings() -> Settings:
    return Settings()

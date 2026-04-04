from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    clash_api_base_url: str = "https://api.clashroyale.com/v1"
    clash_api_token: str = ""
    redis_url: str = "redis://redis:6379/1"
    player_cache_ttl: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()

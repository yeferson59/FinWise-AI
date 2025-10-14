from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Awesome API"
    port: int = 8000
    version: str = "1.0.0"
    environment: str = "development"
    openai_api_key: str = ""
    prefix_api: str = "/api/v1"
    database_url: str = "sqlite:///database.db"
    secret_key: str = ""
    algorithm: str = ""
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return Settings()

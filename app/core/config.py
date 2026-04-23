from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Key Distribution Center"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Session
    SESSION_MAX_AGE: int = 3600  # 1 hour

    # Crypto
    RSA_PRIME_MIN: int = 1000
    RSA_PRIME_MAX: int = 9999
    PRIVATE_KEY_ENCRYPTION_KEY: str = Field(..., env="PRIVATE_KEY_ENCRYPTION_KEY")

    # Message cleanup
    MESSAGE_TTL_MINUTES: int = 5
    CLEANUP_INTERVAL_MINUTES: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
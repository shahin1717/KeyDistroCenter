from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Key Distribution Center"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "sqlite:///./kdc.db"

    # Session
    SESSION_MAX_AGE: int = 3600  # 1 hour

    # Crypto
    RSA_PRIME_MIN: int = 1000
    RSA_PRIME_MAX: int = 9999

    # Message cleanup
    MESSAGE_TTL_MINUTES: int = 5
    CLEANUP_INTERVAL_MINUTES: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
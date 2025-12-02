# app/core/config.py

try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict
except ImportError:
    # Fallback (older installs)
    from pydantic import BaseSettings, ConfigDict


class Settings(BaseSettings):
    # Pydantic v2 configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    # Core settings
    DATABASE_URL: str | None = None
    REDIS_URL: str | None = "redis://redis:6379/1"
    SECRET_KEY: str | None = None

    VAULT_URL: str | None = None
    VAULT_TOKEN: str | None = None

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Postgres
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None

    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = 60

    # Optional
    PGADMIN_DEFAULT_EMAIL: str | None = None
    PGADMIN_DEFAULT_PASSWORD: str | None = None
    VAULT_HEALTH_TEST_PATH: str | None = None


settings = Settings()


# create settings instance at import-time
settings = Settings()

def load_vault_into_settings():
    """
    If you need to populate settings.SECRET_KEY from Vault, call this function
    from app startup code (not at module import time).
    """
    if settings.VAULT_URL and settings.VAULT_TOKEN and not settings.SECRET_KEY:
        # import get_secret here to avoid circular import
        from utils.secrets import get_secret
        val = get_secret("secret/data/myapp", key="SECRET_KEY")
        if val:
            settings.SECRET_KEY = val

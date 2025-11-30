# app/core/config.py
try:
    # pydantic v2.12+ uses pydantic_settings
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict
except ImportError:
    # fallback for older installations
    from pydantic import BaseSettings, ConfigDict


class Settings(BaseSettings):
    # allow extra environment variables instead of failing
    model_config = ConfigDict(extra="allow")

    # app config
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/1"
    SECRET_KEY: str | None = None
    VAULT_URL: str | None = None
    VAULT_TOKEN: str | None = None
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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

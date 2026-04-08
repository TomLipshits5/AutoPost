import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App config
    app_name: str = "AutoPost"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/autopost.db")

    # JWT/Security
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # TikTok API
    tiktok_client_key: str = os.getenv("TIKTOK_CLIENT_KEY", "")
    tiktok_client_secret: str = os.getenv("TIKTOK_CLIENT_SECRET", "")
    tiktok_oauth_redirect_uri: str = os.getenv("TIKTOK_OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/tiktok/callback")
    tiktok_api_base_url: str = "https://open.tiktokapis.com"

    # Upload settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    upload_check_interval: int = int(os.getenv("UPLOAD_CHECK_INTERVAL", "10"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "5"))

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()

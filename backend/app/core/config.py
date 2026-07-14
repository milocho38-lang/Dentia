from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Dentia API"
    app_env: str = "local"
    app_debug: bool = True
    api_prefix: str = "/api"
    log_level: str = "INFO"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "dentia-api"
    jwt_audience: str = "dentia-web"
    access_token_expire_minutes: int = 15
    refresh_token_expire_hours: int = 8
    session_idle_timeout_minutes: int = 60
    auth_max_failed_attempts: int = 5
    auth_lockout_minutes: int = 15
    auth_ip_max_failed_attempts: int = 20
    auth_ip_window_minutes: int = 15
    refresh_cookie_name: str = "dentia_refresh"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: str = "lax"
    refresh_cookie_path: str = "/api/auth"
    branding_storage_dir: str = str(BACKEND_DIR / "storage" / "branding")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes.")
        return value

    @property
    def database_configured(self) -> bool:
        return bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# settings.py -> config -> infrastructure -> shared -> src -> backend -> repo root.
_ENV_FILE = Path(__file__).resolve().parents[5] / ".env"


class Settings(BaseSettings):
    """Config tipada y fail-fast: falta un campo requerido => la app no arranca."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore", frozen=True)

    environment: str = "development"
    frontend_url: str
    cors_origin: str
    database_url: SecretStr

    session_cookie_name: str = "hdm_session"
    session_cookie_secure: bool = False
    session_idle_timeout_seconds: int = 604800
    csrf_cookie_name: str = "hdm_csrf"

    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536
    argon2_parallelism: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings resuelve los requeridos desde el entorno

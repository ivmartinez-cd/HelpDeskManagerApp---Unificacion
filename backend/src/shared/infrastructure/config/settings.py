"""Config tipada y fail-fast de toda la app.

Los campos viven agrupados por tema en `settings_groups.py` (mixins `BaseSettings`) y
`Settings` los compone: pydantic aplana los campos de todas las bases, así que el
contrato público no cambia — `settings.<campo>` y los nombres de las variables de
entorno (el nombre del campo, case-insensitive) son exactamente los mismos que cuando
todo vivía en una sola clase.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from src.shared.infrastructure.config.settings_groups import (
    AuthSettings,
    CanalDirectoSettings,
    ContadoresSettings,
    CoreSettings,
    InsumosSettings,
    MailSettings,
)
from src.shared.infrastructure.config.settings_groups_operativos import (
    AnalisisLogHpSettings,
    LiquidacionesSettings,
    PreventivosSettings,
    SlaSettings,
    WatiSettings,
)

# settings.py -> config -> infrastructure -> shared -> src -> backend -> repo root.
_ENV_FILE = Path(__file__).resolve().parents[5] / ".env"


class Settings(
    CoreSettings,
    AuthSettings,
    MailSettings,
    ContadoresSettings,
    InsumosSettings,
    CanalDirectoSettings,
    SlaSettings,
    PreventivosSettings,
    WatiSettings,
    AnalisisLogHpSettings,
    LiquidacionesSettings,
):
    """Config tipada y fail-fast: falta un campo requerido => la app no arranca."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _cookie_secure_por_entorno(cls, data: object) -> object:
        """`SESSION_COOKIE_SECURE` sin definir vale `true` fuera de development:
        olvidar la variable en producción no puede dejar la sesión de 7 días
        viajando en claro (ronda E2E 2026-09-05). En dev el default sigue
        siendo `false` y un valor explícito siempre gana."""
        if not isinstance(data, dict) or "session_cookie_secure" in data:
            return data
        if str(data.get("environment", "development")) == "development":
            return data
        return {**data, "session_cookie_secure": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings resuelve los requeridos desde el entorno

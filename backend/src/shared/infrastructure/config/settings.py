"""Config tipada y fail-fast de toda la app.

Los campos viven agrupados por tema en `settings_groups.py` (mixins `BaseSettings`) y
`Settings` los compone: pydantic aplana los campos de todas las bases, así que el
contrato público no cambia — `settings.<campo>` y los nombres de las variables de
entorno (el nombre del campo, case-insensitive) son exactamente los mismos que cuando
todo vivía en una sola clase.
"""

from functools import lru_cache
from pathlib import Path

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings resuelve los requeridos desde el entorno

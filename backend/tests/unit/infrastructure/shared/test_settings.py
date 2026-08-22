"""`Settings` se compone de mixins por tema (settings_groups.py): estos tests fijan
el contrato que el resto del código asume — los campos son atributos planos de
`Settings`, cada uno se resuelve desde la variable de entorno con su mismo nombre
(case-insensitive), y la config final (env_file, extra="ignore", frozen=True) se
aplica aunque los mixins no la declaren."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings

from src.shared.infrastructure.config import settings_groups
from src.shared.infrastructure.config.settings import Settings

_MINIMO = {
    "FRONTEND_URL": "http://front.test",
    "CORS_ORIGIN": "http://front.test",
    "DATABASE_URL": "postgresql+asyncpg://x:x@localhost/x",
}


def _settings(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    for key, value in {**_MINIMO, **env}.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_campos_clave_existen_con_su_tipo(monkeypatch: pytest.MonkeyPatch) -> None:
    # El contenedor de dev trae su propio entorno (SMTP_PORT, DISABLE_BACKGROUND_JOBS…):
    # acá se verifica tipo y presencia de los campos, no sus valores por default.
    s = _settings(monkeypatch)

    assert isinstance(s.environment, str) and isinstance(s.frontend_url, str)
    assert isinstance(s.database_url, SecretStr)
    assert isinstance(s.smtp_pass, SecretStr) and isinstance(s.smtp_port, int)
    assert isinstance(s.session_cookie_name, str)
    assert isinstance(s.sds_delete_dry_run, bool) and isinstance(s.disable_background_jobs, bool)
    assert isinstance(s.sla_mercurio_timeout_seconds, float)
    assert isinstance(s.wati_poll_interval_minutes, int)
    assert isinstance(s.app_timezone, str)


def test_defaults_declarados_no_cambiaron() -> None:
    campos = Settings.model_fields
    assert campos["environment"].default == "development"
    assert campos["smtp_port"].default == 587
    assert campos["session_cookie_name"].default == "hdm_session"
    assert campos["sds_delete_dry_run"].default is True
    assert campos["disable_background_jobs"].default is False
    assert campos["wati_poll_interval_minutes"].default == 3
    assert campos["app_timezone"].default == "America/Argentina/Buenos_Aires"
    assert {n for n, f in campos.items() if f.is_required()} == {
        "frontend_url",
        "cors_origin",
        "database_url",
    }


def test_campos_se_leen_del_entorno_con_su_mismo_nombre(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    s = _settings(
        monkeypatch,
        ENVIRONMENT="production",
        SMTP_HOST="mailpit",
        DISABLE_BACKGROUND_JOBS="true",
        SLA_MERCURIO_HOST="SERVIDOR,1434",
        GOOGLE_MAPS_MAX_CALLS_PER_RUN="7",
        WATI_API_TOKEN="tok",
    )

    assert s.environment == "production"
    assert s.smtp_host == "mailpit"
    assert s.disable_background_jobs is True
    assert s.sla_mercurio_host == "SERVIDOR,1434"
    assert s.google_maps_max_calls_per_run == 7
    assert s.wati_api_token.get_secret_value() == "tok"


def test_requeridos_sin_default_hacen_fallar_el_arranque(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in _MINIMO:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]
    faltantes = {e["loc"][0] for e in exc_info.value.errors()}
    assert faltantes == {"frontend_url", "cors_origin", "database_url"}


def test_config_final_y_campos_planos(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(monkeypatch, CAMPO_INEXISTENTE="x")

    assert Settings.model_config["extra"] == "ignore"
    assert Settings.model_config["frozen"] is True
    assert isinstance(Settings.model_config["env_file"], Path)
    assert not hasattr(s, "campo_inexistente")
    with pytest.raises(ValidationError):
        s.environment = "otro"  # type: ignore[misc]

    mixins = [
        cls
        for cls in vars(settings_groups).values()
        if isinstance(cls, type) and issubclass(cls, BaseSettings) and cls is not BaseSettings
    ]
    assert mixins and all(issubclass(Settings, m) for m in mixins)
    campos_mixins = {f for m in mixins for f in m.model_fields}
    assert campos_mixins == set(Settings.model_fields)
    assert all(not m.model_config.get("frozen") for m in mixins)

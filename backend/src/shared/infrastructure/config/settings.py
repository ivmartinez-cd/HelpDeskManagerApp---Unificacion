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

    # SMTP_HOST vacío = mailer de consola (dev); con host, SmtpMailer real.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: SecretStr = SecretStr("")
    smtp_from: str = "HelpDesk Manager <no-reply@cdsa.com.ar>"

    contadores_output_dir: str = "var/contadores/outputs"

    sds_api_key: str = "2bc8f5eaae344c46814190bffd40060d"
    sds_api_secret: SecretStr = SecretStr(
        "0iIxVYcz5lH8sTjl6c6B89uvyQ4qyl2bojRPv155onzqkqpANt6culpITUBldR8a"
    )
    sds_base_url: str = "https://hp-sds-latam.insightportal.net/PortalAPI"
    sds_timeout_seconds: float = 20.0

    # Módulo insumos — misma Insight Portal API que sds_* de contadores (misma base
    # URL; la pregunta abierta de Fase 1 sobre si eran la misma integración quedó
    # confirmada), pero cada módulo mantiene su propio bloque de config y su propio
    # cliente: los módulos de negocio son independientes entre sí (import-linter).
    insight_base_url: str = "https://hp-sds-latam.insightportal.net/PortalAPI"
    insight_api_key: str = ""
    insight_api_secret: SecretStr = SecretStr("")
    # INSIGHT_STATUS_ON_ORDER: nótese ACTION, no ACTIONED (bug corregido en el legacy).
    insight_mark_actioned: bool = False
    insight_status_on_order: str = "ACTION"

    # Canal Directo (pedidos SOAP wsAyC + contactos globales de fallback).
    cd_base_url: str = "https://webagentes.canaldirecto.com.ar"
    cd_origen_id: str = "3"  # 3 = Interno — el objetivo entero de usar el SOAP
    cd_motivo_id: str = "1"
    cd_solicitante_apellido: str = ""
    cd_solicitante_nombre: str = ""
    cd_solicitante_telefono: str = ""
    cd_solicitante_email: str = ""
    cd_solicitante_sector: str = ""
    cd_destinatario_apellido: str = ""
    cd_destinatario_nombre: str = ""
    cd_destinatario_telefono: str = ""
    cd_destinatario_email: str = ""
    cd_destinatario_sector: str = ""

    app_timezone: str = "America/Argentina/Buenos_Aires"
    # Cadencia del poller de insumos; el dashboard la publica como refreshMinutes.
    # El legacy defaulteaba 120 en código pero el .env recomienda 60 (SDS lee niveles
    # cada 1 hora, KB HP 30000040938).
    poll_interval_minutes: int = 60

    epson_ers_username: str = "insumos@canaldirecto.com.ar"
    epson_ers_password: SecretStr = SecretStr("C@nal3160")
    epson_ers_base_url: str = "https://www.remote-services.epson.com/prod"
    epson_ers_token_file: str = "var/contadores/ers_token.json"
    epson_ers_timeout_seconds: float = 15.0

    gestion_web_base_url: str = "http://gestion.cdsa.com.ar"
    gestion_web_username: str = ""
    gestion_web_password: SecretStr = SecretStr("")
    gestion_web_timeout_seconds: float = 15.0
    # Sesión (PHPSESSID) renovada automáticamente por gestion_session_refresher
    # vía login Symfony estándar — reemplaza el cookie pegado a mano que vencía.
    gestion_session_file: str = "var/contadores/gestion_session.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings resuelve los requeridos desde el entorno

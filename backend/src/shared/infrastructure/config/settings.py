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
    # URL y mismo flujo de login), pero **cliente de API registrado aparte**: probado
    # en vivo (2026-08-11) que el par de contadores SÍ autentica, pero el par propio de
    # SDSInsumos (rescatado de su .env real, no el .env.example) es el correcto para
    # este módulo — cada app parece tener su propio client id/secret contra el mismo
    # backend HP. Cada módulo mantiene su propio bloque de config y su propio cliente
    # de todas formas por la independencia entre módulos de negocio (import-linter).
    insight_base_url: str = "https://hp-sds-latam.insightportal.net/PortalAPI"
    insight_api_key: str = "cbcf148472e74e868c44199f507aa2f7"
    insight_api_secret: SecretStr = SecretStr(
        "Ra5tjX4UbZNbpRMzVGKrN1KcBsLDJFOYvJzWNwqk5ukbdlxrJthO7NxqthNSM4Yr"
    )
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

    # Módulo sla — consulta en vivo a la base Siges del SQL Server MERCURIO.
    # Sin host configurado los endpoints de sla responden 502 con mensaje claro
    # (ver get_sla_query_gateway); el default vacío evita romper el arranque de
    # los demás módulos en entornos sin acceso a esa red. `host` admite
    # "SERVIDOR,puerto" si no es el 1433 default.
    sla_mercurio_host: str = ""
    sla_mercurio_database: str = "Siges"
    sla_mercurio_user: str = ""
    sla_mercurio_password: SecretStr = SecretStr("")
    sla_mercurio_driver: str = "{ODBC Driver 18 for SQL Server}"
    # SQL Server legacy sin certificado confiable: el driver 18 encripta por
    # default y el handshake falla; apagado replica el comportamiento del
    # driver 17 con el que se consultaba esta base hasta ahora.
    sla_mercurio_encrypt: bool = False
    sla_mercurio_timeout_seconds: float = 30.0

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

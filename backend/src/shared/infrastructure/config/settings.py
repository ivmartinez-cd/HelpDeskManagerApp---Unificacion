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
    analisis_log_hp_cpmd_dir: str = "var/analisis_log_hp/cpmd"

    # Credenciales solo por .env — nunca defaults en código (§8; los valores que
    # vivieron acá hasta 2026-08-16 quedan en el historial git: rotarlos).
    sds_api_key: str = ""
    sds_api_secret: SecretStr = SecretStr("")
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
    # Válvula de seguridad económica de la auto-carga: tope de pedidos/incidentes
    # reales por ciclo del poller, ante datos anómalos de SDS. A diferencia de
    # autoload_enabled/max_days/min_percent (settings de UI en app_settings), esto es
    # una válvula operativa — mismo criterio que el legacy (AUTOLOAD_MAX_ORDERS_PER_CYCLE).
    autoload_max_orders_per_cycle: int = 10

    epson_ers_username: str = ""
    epson_ers_password: SecretStr = SecretStr("")
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
    # Tope de consultas simultáneas a MERCURIO de todo el proceso (semáforo del
    # MercurioQueryRunner compartido, ADR-018). Sin prefijo sla_ porque es
    # config nueva de toda la app, no del módulo sla.
    mercurio_max_concurrent: int = 3

    # Zonas de `Sucursal.Cuadricula` fuera del alcance de preventivos locales
    # (PSTs del interior, agrupaciones y basura de carga). "X*" excluye por
    # prefijo; el resto es igualdad exacta. Es lista de EXCLUSIÓN a propósito:
    # una zona local nueva (p. ej. NORTE5) aparece sola sin tocar nada.
    preventivos_zonas_excluidas: str = (
        "INTERIOR,A DEFINIR,PROPIO,KIKO,0000000000,BSAS.*,CBA..*,CUYO.*,NOA..*,COSTA*"
    )
    # "Cliente vivo" para preventivos: alguna toma de contador O algún
    # incidente de la empresa dentro de esta ventana. Es la única señal que
    # distingue la baja de facto (Garbarino: todo figura activo en Gestión
    # pero sin actividad desde 2022) — ver ADR-019 y rondas 7-11.
    preventivos_meses_actividad: int = 3

    # SOAP wsAyC de Canal Directo — mismo endpoint/WSDL para insumos y
    # liquidaciones (provider compartido, ADR-018). Defaults = los valores que
    # estaban hardcodeados en los gateways; no hace falta tocar ningún .env.
    wsayc_wsdl_url: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
    wsayc_endpoint: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php"
    wsayc_timeout_seconds: float = 30.0
    # Cadencia del job de fondo que refresca el snapshot del período actual —
    # sin esto, Inicio y /sla pegarían en vivo contra MERCURIO (~40s) en cada
    # carga. El botón "Actualizar" siempre fuerza un refresh inmediato aparte.
    sla_refresh_interval_minutes: int = 240
    # Cadencia del job de fondo que refresca el backlog de incidentes sin cerrar.
    # Más frecuente que SLA porque cambia en tiempo real (cada cierre en Gestión
    # actualiza el backlog). Corte temporal: cuántos meses atrás buscar en Siges.
    pendientes_refresh_interval_minutes: int = 60
    pendientes_meses_corte: int = 24
    # Cadencia del job de fondo que refresca la copia local de eventos del
    # Calendario de Planificación. Full replace de ±90 días (~20 s); Gestión no
    # expone diff, así que cada ciclo rehace el rango entero. El botón
    # "Sincronizar" fuerza un ciclo inmediato aparte.
    calendario_refresh_interval_minutes: int = 120

    # PortalWeb de SDS Insight — scraping para baja de equipos offline.
    # sds_delete_dry_run=True por default: la baja real es irreversible. Solo cambiar a
    # False con una decisión explícita (no hay entorno de prueba HP para validar).
    sds_portal_base_url: str = "https://hp-sds-latam.insightportal.net"
    sds_portal_username: str = ""
    sds_portal_password: SecretStr = SecretStr("")
    sds_delete_dry_run: bool = True

    gestion_web_base_url: str = "http://gestion.cdsa.com.ar"
    gestion_web_username: str = ""
    gestion_web_password: SecretStr = SecretStr("")
    gestion_web_timeout_seconds: float = 15.0
    # Sesión (PHPSESSID) renovada automáticamente por gestion_session_refresher
    # vía login Symfony estándar — reemplaza el cookie pegado a mano que vencía.
    gestion_session_file: str = "var/contadores/gestion_session.json"

    # Emails del módulo vacaciones (nueva solicitud → jefes+admins, decisión →
    # empleado). Default False a propósito: en dev el .env tiene SMTP real y la
    # DB puede tener destinatarios reales — activarlo es una decisión explícita
    # por entorno, no un default (mismo criterio que el modo test de CLAUDE.md).
    vacaciones_mail_enabled: bool = False

    # Módulo analisis-log-hp — diagnóstico IA con Anthropic.
    # Sin clave configurada los endpoints de IA responden 502 con mensaje claro.
    anthropic_api_key: str = ""
    # Cadencia del job de snapshots SDS automáticos (2×/día = cada 720 min).
    analisis_log_hp_snapshot_interval_minutes: int = 720

    # Google Maps (Distance Matrix + Geocoding) — usadas por el módulo de
    # liquidaciones para calcular distancias PST↔sucursal cliente y geocodificar
    # sucursales sin pin en Siges. Sin clave configurada los endpoints responden
    # 502 con mensaje claro. La key es corporativa y paga: el tope corta una
    # corrida antes de superar ese número de unidades facturables (requests de
    # geocoding + elementos de matrix).
    google_maps_api_key: str = ""
    google_maps_max_calls_per_run: int = 200

    # Georef (API del Estado argentino, gratuita/sin auth) — Tier 1 de
    # geovalidación. Sin costo, pero sin abuso de un servicio público: tope
    # por corrida acota la duración del request HTTP (no por dinero, por
    # tiempo), y la pausa entre llamadas es cortesía hacia el servicio.
    georef_max_calls_per_run: int = 200
    georef_pausa_segundos: float = 0.2

    # Nominatim (OpenStreetMap, gratuito) — Tier 1b, segunda opinión SOLO
    # sobre lo que Georef ya marcó incompatible (nunca el universo completo).
    # El rate limit real de 1 req/s lo aplica el adapter mismo; este tope es
    # para no bloquear el request HTTP demasiado tiempo (60 = ~1 minuto).
    nominatim_max_calls_per_run: int = 60

    # Cadencia del job de fondo que reconcilia contra AyC las liquidaciones
    # pendientes de todos los prestadores vinculados (estado, costos/km de
    # incidentes) — mismo caso de uso que el botón "Sincronizar CD", pero sin
    # la fase de detección de anuladas (esa queda exclusiva del botón manual,
    # con el usuario mirando). El universo típico es chico (~5 pendientes hoy),
    # 2h alcanza sin generar carga SOAP relevante.
    liquidaciones_reconciliar_interval_minutes: int = 120

    # Desactiva todos los jobs de fondo (útil en CI/test o cuando se corren
    # múltiples instancias y solo una debe ejecutar los jobs).
    disable_background_jobs: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings resuelve los requeridos desde el entorno

"""Grupos temáticos de campos de `Settings` (mixins, ver settings.py).

Cada clase es un `BaseSettings` sin `model_config` propio que nunca se instancia por
separado: `Settings` las compone y pydantic aplana sus campos, así que el nombre de
cada campo sigue siendo, tal cual, el nombre de su variable de entorno
(case-insensitive) y el atributo `settings.<campo>` que usa el resto del código.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class CoreSettings(BaseSettings):
    """Entorno, URLs base, DB y switches de proceso."""

    environment: str = "development"
    frontend_url: str
    cors_origin: str
    database_url: SecretStr
    app_timezone: str = "America/Argentina/Buenos_Aires"
    # Desactiva todos los jobs de fondo (útil en CI/test o cuando se corren
    # múltiples instancias y solo una debe ejecutar los jobs).
    disable_background_jobs: bool = False
    # Insumos es el único módulo cuyo poller manda mail real a destinatarios
    # de logística (ver incidente 2026-08-12) y opera sobre datos sembrados
    # de producción — se puede mantener apagado mientras el resto de los
    # jobs de sincronización corre normalmente.
    disable_insumos_background_jobs: bool = False


class AuthSettings(BaseSettings):
    """Sesión, CSRF y hashing de contraseñas."""

    session_cookie_name: str = "hdm_session"
    session_cookie_secure: bool = False
    session_idle_timeout_seconds: int = 604800
    csrf_cookie_name: str = "hdm_csrf"

    argon2_time_cost: int = 3
    argon2_memory_cost_kib: int = 65536
    argon2_parallelism: int = 4


class MailSettings(BaseSettings):
    """SMTP y switches de envío por módulo."""

    # SMTP_HOST vacío = mailer de consola (dev); con host, SmtpMailer real.
    # En dev el host es el contenedor `mailpit` (compose): SMTP_STARTTLS=false y
    # sin usuario — ningún mail sale de la máquina. Default true = producción.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: SecretStr = SecretStr("")
    smtp_starttls: bool = True
    smtp_from: str = "HelpDesk Manager <no-reply@cdsa.com.ar>"

    cd_smtp_host: str = ""  # SMTP institucional de Canal Directo; ver .env.example CD_SMTP_*
    cd_smtp_port: int = 25
    cd_smtp_user: str = ""
    cd_smtp_pass: SecretStr = SecretStr("")
    cd_smtp_starttls: bool = False
    cd_smtp_from: str = "Canal Directo <noreply@canaldirecto.com.ar>"

    # Emails del módulo vacaciones (nueva solicitud → jefes+admins, decisión →
    # empleado). Default False a propósito: en dev el .env tiene SMTP real y la
    # DB puede tener destinatarios reales — activarlo es una decisión explícita
    # por entorno, no un default (mismo criterio que el modo test de CLAUDE.md).
    vacaciones_mail_enabled: bool = False

    # SMTP dedicado del aviso de aprobación de liquidaciones (jpcorigliano@
    # canaldirecto.com.ar) — separado de CD_SMTP_* a propósito (decisión
    # 2026-09-03): CD_SMTP_* también lo usa el reset/activación de clave de
    # auth, y este dev lo prueban varios compañeros; querer mail real solo acá
    # sin arrastrar auth necesita su propio host. Vacío = cae a
    # get_mailer_canal_directo() (CD_SMTP_*, hoy Mailpit en dev).
    liquidaciones_smtp_host: str = ""
    liquidaciones_smtp_port: int = 25
    liquidaciones_smtp_user: str = ""
    liquidaciones_smtp_pass: SecretStr = SecretStr("")
    liquidaciones_smtp_starttls: bool = False
    liquidaciones_smtp_from: str = "Canal Directo <noreply@canaldirecto.com.ar>"


class ContadoresSettings(BaseSettings):
    """Módulo contadores: SDS Insight API, Epson ERS y Gestión web."""

    contadores_output_dir: str = "var/contadores/outputs"

    # Credenciales solo por .env — nunca defaults en código (§8; los valores que
    # vivieron acá hasta 2026-08-16 quedan en el historial git: rotarlos).
    sds_api_key: str = ""
    sds_api_secret: SecretStr = SecretStr("")
    sds_base_url: str = "https://hp-sds-latam.insightportal.net/PortalAPI"
    sds_timeout_seconds: float = 20.0

    epson_ers_username: str = ""
    epson_ers_password: SecretStr = SecretStr("")
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


class InsumosSettings(BaseSettings):
    """Módulo insumos: Insight Portal API, poller y PortalWeb de SDS."""

    # Misma Insight Portal API que sds_* de contadores (misma base URL y mismo flujo
    # de login), pero **cliente de API registrado aparte**: probado en vivo
    # (2026-08-11) que el par de contadores SÍ autentica, pero el par propio de
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

    # Cadencia del poller de insumos; el dashboard la publica como refreshMinutes.
    # El legacy defaulteaba 120 en código pero el .env recomienda 60 (SDS lee niveles
    # cada 1 hora, KB HP 30000040938).
    poll_interval_minutes: int = 60
    # Válvula de seguridad económica de la auto-carga: tope de pedidos/incidentes
    # reales por ciclo del poller, ante datos anómalos de SDS. A diferencia de
    # autoload_enabled/max_days/min_percent (settings de UI en app_settings), esto es
    # una válvula operativa — mismo criterio que el legacy (AUTOLOAD_MAX_ORDERS_PER_CYCLE).
    autoload_max_orders_per_cycle: int = 10

    # PortalWeb de SDS Insight — scraping para baja de equipos offline.
    # sds_delete_dry_run=True por default: la baja real es irreversible. Solo cambiar a
    # False con una decisión explícita (no hay entorno de prueba HP para validar).
    sds_portal_base_url: str = "https://hp-sds-latam.insightportal.net"
    sds_portal_username: str = ""
    sds_portal_password: SecretStr = SecretStr("")
    sds_delete_dry_run: bool = True

    # Aviso por mail al cliente cuando la app carga un pedido de insumos (ver
    # domain/value_objects/client_order_notice.py) — SMTP dedicado, separado del
    # SMTP_* interno (backup/alertas a destinatarios internos): este manda a clientes
    # externos y necesita su propio remitente/relay. Vacío = feature deshabilitada,
    # mismo criterio que smtp_host vacío para los mails internos.
    client_mail_smtp_host: str = ""
    client_mail_smtp_port: int = 587
    client_mail_smtp_username: str = ""
    client_mail_smtp_password: SecretStr = SecretStr("")
    # False para relays de prueba sin STARTTLS (ej. Mailpit).
    client_mail_smtp_use_tls: bool = True
    client_mail_sender_email: str = "insumos@canaldirecto.com.ar"


class CanalDirectoSettings(BaseSettings):
    """Canal Directo: pedidos SOAP wsAyC (provider compartido, ADR-018) y contactos."""

    cd_base_url: str = "https://webagentes.canaldirecto.com.ar"
    # 6 = Proactivo, alta 2026-08 exclusiva para esta app: a diferencia de 3 (Interno,
    # valor original), es visible en getTopSupplies/AyC/portal — ver order_settings.py.
    cd_origen_id: str = "6"
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
    # Base del portal de CLIENTES (distinto de cd_base_url, que es WebAgentes/interno)
    # — solo para armar el link al pedido en el mail de aviso al cliente.
    cd_clientes_url: str = "https://webclientes.canaldirecto.com.ar"

    # SOAP wsAyC — mismo endpoint/WSDL para insumos y liquidaciones. Defaults = los
    # valores que estaban hardcodeados en los gateways; no hace falta tocar ningún .env.
    wsayc_wsdl_url: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
    wsayc_endpoint: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php"
    wsayc_timeout_seconds: float = 30.0


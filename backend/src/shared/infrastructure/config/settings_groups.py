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

    # Emails del módulo vacaciones (nueva solicitud → jefes+admins, decisión →
    # empleado). Default False a propósito: en dev el .env tiene SMTP real y la
    # DB puede tener destinatarios reales — activarlo es una decisión explícita
    # por entorno, no un default (mismo criterio que el modo test de CLAUDE.md).
    vacaciones_mail_enabled: bool = False


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

    # SOAP wsAyC — mismo endpoint/WSDL para insumos y liquidaciones. Defaults = los
    # valores que estaban hardcodeados en los gateways; no hace falta tocar ningún .env.
    wsayc_wsdl_url: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php?wsdl"
    wsayc_endpoint: str = "https://wsg.cdsisa.com.ar/wsAyC_server.php"
    wsayc_timeout_seconds: float = 30.0


class SlaSettings(BaseSettings):
    """Módulo sla: base Siges (SQL Server MERCURIO) y jobs de refresco."""

    # Consulta en vivo a la base Siges del SQL Server MERCURIO. Sin host configurado
    # los endpoints de sla responden 502 con mensaje claro (ver get_sla_query_gateway);
    # el default vacío evita romper el arranque de los demás módulos en entornos sin
    # acceso a esa red. `host` admite "SERVIDOR,puerto" si no es el 1433 default.
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

    # Cadencia del job de fondo que refresca el snapshot del período actual —
    # sin esto, Inicio y /sla pegarían en vivo contra MERCURIO (~40s) en cada
    # carga. El botón "Actualizar" siempre fuerza un refresh inmediato aparte.
    sla_refresh_interval_minutes: int = 240
    # Cadencia del job de fondo que refresca el backlog de incidentes sin cerrar.
    # Más frecuente que SLA porque cambia en tiempo real (cada cierre en Gestión
    # actualiza el backlog). Corte temporal: cuántos meses atrás buscar en Siges.
    pendientes_refresh_interval_minutes: int = 60
    pendientes_meses_corte: int = 24
    # ID_Empresa de 'CD - Mesa de Ayuda' en dbo.Empresa — juega el rol de
    # técnico (Incidente.ID_Tecnico) para sus incidentes. Confirmado 2026-08-25.
    mesa_ayuda_siges_empresa_id: int = 428
    # Cadencia del job de fondo que refresca la copia local de eventos del
    # Calendario de Planificación. Full replace de ±90 días (~20 s); Gestión no
    # expone diff, así que cada ciclo rehace el rango entero. El botón
    # "Sincronizar" fuerza un ciclo inmediato aparte.
    calendario_refresh_interval_minutes: int = 120


class PreventivosSettings(BaseSettings):
    """Módulo preventivos: alcance de zonas y ventana de actividad."""

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


class WatiSettings(BaseSettings):
    """Módulo wati: chats de WhatsApp esperando respuesta."""

    # Polling de solo lectura contra la API V1 de WATI; no hay webhook porque IT no
    # expone URL pública. WATI_URL es la misma variable que usa el frontend para el
    # ícono del header: acá sirve para linkear al Team Inbox desde la card.
    # Token: generarlo en Connector → API con scopes de solo lectura
    # (contacts:read, conversations:read) y con fecha de vencimiento.
    wati_api_base_url: str = "https://live-mt-server.wati.io"
    wati_tenant_id: str = ""
    wati_api_token: SecretStr = SecretStr("")
    wati_url: str = ""
    wati_poll_interval_minutes: int = 3
    wati_ventana_horas: int = 48
    wati_max_contactos_por_ciclo: int = 60
    # Rate limit publicado por WATI: 10 req / 10 s en getContacts/getMessages.
    wati_request_spacing_seconds: float = 1.1
    wati_timeout_seconds: float = 20.0


class AnalisisLogHpSettings(BaseSettings):
    """Módulo analisis-log-hp: diagnóstico IA con Anthropic y snapshots SDS."""

    analisis_log_hp_cpmd_dir: str = "var/analisis_log_hp/cpmd"
    # Sin clave configurada los endpoints de IA responden 502 con mensaje claro.
    anthropic_api_key: str = ""
    # Cadencia del job de snapshots SDS automáticos (2×/día = cada 720 min).
    analisis_log_hp_snapshot_interval_minutes: int = 720


class LiquidacionesSettings(BaseSettings):
    """Módulo liquidaciones: geocodificación (Google Maps, Georef, Nominatim) y jobs."""

    # Google Maps (Distance Matrix + Geocoding) — distancias PST↔sucursal cliente y
    # geocodificación de sucursales sin pin en Siges. Sin clave configurada los
    # endpoints responden 502 con mensaje claro. La key es corporativa y paga: el tope
    # corta una corrida antes de superar ese número de unidades facturables (requests
    # de geocoding + elementos de matrix).
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

"""Piezas compartidas por todas las factories del módulo insumos.

Los gateways son singletons de proceso a propósito: ZeepWsAycGateway cachea el cliente
zeep (cargar el WSDL es caro) y HttpxInsightGateway cachea el token con su margen de
refresco — recrearlos por request tiraría ambos caches.

Vive separado de `dependencies.py` para que ese archivo pueda crecer con un builder
por caso de uso sin pasarse del máximo de líneas.
"""

from functools import lru_cache
from zoneinfo import ZoneInfo

from src.modules.insumos.application.dtos.pending_orders import PendingOrderRow
from src.modules.insumos.domain.repositories.client_order_notifier import ClientOrderNotifier
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.infrastructure.client_order_mailer import ClientOrderMailer
from src.modules.insumos.infrastructure.insight.httpx_insight_gateway import HttpxInsightGateway
from src.modules.insumos.infrastructure.portal.httpx_sds_portal_gateway import (
    HttpxSdsPortalGateway,
)
from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.modules.insumos.presentation.client_order_dispatch import ClientOrderDispatcher
from src.shared.infrastructure.cache.ttl_cache import TTLCache
from src.shared.infrastructure.config.settings import Settings, get_settings
from src.shared.infrastructure.database.engine import get_engine
from src.shared.infrastructure.locks.postgres_advisory_lock import (
    OFFLINE_DELETE_LOCK_KEY,
    OFFLINE_VERIFY_LOCK_KEY,
    PostgresAdvisoryLock,
)


@lru_cache
def app_timezone() -> ZoneInfo:
    """El "hoy" de negocio y el horario laboral se miden en esta zona, nunca en la del
    contenedor. Cacheado: parsear la tzdata una vez por proceso alcanza."""
    return ZoneInfo(get_settings().app_timezone)


@lru_cache
def get_wsayc_gateway() -> ZeepWsAycGateway:
    return ZeepWsAycGateway()


@lru_cache
def get_insight_gateway() -> HttpxInsightGateway:
    settings = get_settings()
    return HttpxInsightGateway(
        settings.insight_base_url,
        settings.insight_api_key,
        settings.insight_api_secret.get_secret_value(),
    )


@lru_cache
def get_sds_portal_gateway() -> HttpxSdsPortalGateway:
    settings = get_settings()
    return HttpxSdsPortalGateway(
        base_url=settings.sds_portal_base_url,
        username=settings.sds_portal_username,
        password=settings.sds_portal_password.get_secret_value(),
    )


@lru_cache
def get_offline_verify_lock() -> PostgresAdvisoryLock:
    return PostgresAdvisoryLock(get_engine(), OFFLINE_VERIFY_LOCK_KEY)


@lru_cache
def get_offline_delete_lock() -> PostgresAdvisoryLock:
    return PostgresAdvisoryLock(get_engine(), OFFLINE_DELETE_LOCK_KEY)


@lru_cache
def get_pending_orders_cache() -> TTLCache[tuple[int | None, bool], list[PendingOrderRow]]:
    """compute_pending_orders (ver list_pending_orders.py) pega en vivo contra SOAP +
    Insight — TTL corto (no el intervalo del poller: acá importa el seguimiento día a
    día) solo para absorber pedidos casi simultáneos: GET al entrar a la pestaña, el
    polling del frontend y el job de aviso de pedidos por vencer compitiendo por el
    mismo cómputo. Singleton de proceso: @lru_cache sobre una función sin argumentos
    devuelve siempre la misma instancia, compartida por todos los callers."""
    return TTLCache(ttl_seconds=60)


@lru_cache
def get_client_order_notifier() -> ClientOrderNotifier | None:
    """None si CLIENT_MAIL_SMTP_HOST no está configurado — el feature queda
    deshabilitada sin tocar el resto del flujo de carga (ver LoadOrderPorts)."""
    settings = get_settings()
    if not settings.client_mail_smtp_host:
        return None
    return ClientOrderDispatcher(ClientOrderMailer(settings))


def order_settings(settings: Settings) -> CanalDirectoOrderSettings:
    return CanalDirectoOrderSettings(
        solicitante=ContactInfo(
            apellido=settings.cd_solicitante_apellido,
            nombre=settings.cd_solicitante_nombre,
            telefono=settings.cd_solicitante_telefono,
            email=settings.cd_solicitante_email,
            sector=settings.cd_solicitante_sector,
        ),
        destinatario=ContactInfo(
            apellido=settings.cd_destinatario_apellido,
            nombre=settings.cd_destinatario_nombre,
            telefono=settings.cd_destinatario_telefono,
            email=settings.cd_destinatario_email,
            sector=settings.cd_destinatario_sector,
        ),
        origen_id=settings.cd_origen_id,
        motivo_id=settings.cd_motivo_id,
        portal_base_url=settings.cd_base_url,
    )

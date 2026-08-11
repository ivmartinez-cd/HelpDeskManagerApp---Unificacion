"""Piezas compartidas por todas las factories del módulo insumos.

Los gateways son singletons de proceso a propósito: ZeepWsAycGateway cachea el cliente
zeep (cargar el WSDL es caro) y HttpxInsightGateway cachea el token con su margen de
refresco — recrearlos por request tiraría ambos caches.

Vive separado de `dependencies.py` para que ese archivo pueda crecer con un builder
por caso de uso sin pasarse del máximo de líneas.
"""

from functools import lru_cache
from zoneinfo import ZoneInfo

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.infrastructure.insight.httpx_insight_gateway import HttpxInsightGateway
from src.modules.insumos.infrastructure.soap.zeep_wsayc_gateway import ZeepWsAycGateway
from src.shared.infrastructure.config.settings import Settings, get_settings


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

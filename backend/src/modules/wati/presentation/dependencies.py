"""Factories del módulo wati. El gateway es singleton de proceso (`lru_cache`)
porque serializa las llamadas para respetar el rate limit de WATI: dos
instancias no sabrían una de la otra."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.wati.application.use_cases.get_pendientes_resumen import GetPendientesResumen
from src.modules.wati.application.use_cases.list_pendientes import ListPendientes
from src.modules.wati.application.use_cases.sync_conversaciones import SyncConversaciones
from src.modules.wati.infrastructure.repositories.sqlalchemy_conversacion_repository import (
    SqlAlchemyConversacionRepository,
)
from src.modules.wati.infrastructure.wati_api.httpx_wati_gateway import HttpxWatiGateway
from src.shared.infrastructure.config.settings import get_settings


@lru_cache
def get_wati_gateway() -> HttpxWatiGateway:
    settings = get_settings()
    return HttpxWatiGateway(
        settings.wati_api_base_url,
        settings.wati_tenant_id,
        settings.wati_api_token.get_secret_value(),
        spacing_seconds=settings.wati_request_spacing_seconds,
        timeout_seconds=settings.wati_timeout_seconds,
    )


def build_list_pendientes(session: AsyncSession) -> ListPendientes:
    return ListPendientes(SqlAlchemyConversacionRepository(session))


def build_get_pendientes_resumen(session: AsyncSession) -> GetPendientesResumen:
    return GetPendientesResumen(
        SqlAlchemyConversacionRepository(session), build_list_pendientes(session)
    )


def build_sync_conversaciones(session: AsyncSession) -> SyncConversaciones:
    settings = get_settings()
    return SyncConversaciones(
        get_wati_gateway(),
        SqlAlchemyConversacionRepository(session),
        ventana_horas=settings.wati_ventana_horas,
        max_por_ciclo=settings.wati_max_contactos_por_ciclo,
    )

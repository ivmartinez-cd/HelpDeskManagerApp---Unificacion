"""Factories del módulo reporte_incidentes. El gateway SOAP es singleton de
proceso (`lru_cache`): comparte su caché en memoria y su semáforo."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import ArmarReporte
from src.modules.reporte_incidentes.infrastructure.repositories.sqlalchemy_taxonomia import (
    SqlAlchemyTaxonomiaRepository,
)
from src.modules.reporte_incidentes.infrastructure.repositories.sqlalchemy_tipificaciones import (
    SqlAlchemyTipificacionCacheRepository,
)
from src.modules.reporte_incidentes.infrastructure.wsayc.zeep_incidentes_gateway import (
    ZeepIncidentesGateway,
)
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.wsayc.client_provider import get_wsayc_client_provider


@lru_cache
def get_incidentes_gateway() -> ZeepIncidentesGateway:
    settings = get_settings()
    return ZeepIncidentesGateway(
        get_wsayc_client_provider(),
        settings.reporte_incidentes_concurrencia_soap,
        settings.reporte_incidentes_cache_ttl_segundos,
    )


def build_armar_reporte(session: AsyncSession) -> ArmarReporte:
    repos = (
        SqlAlchemyTaxonomiaRepository(session),
        SqlAlchemyTipificacionCacheRepository(session),
    )
    return ArmarReporte(
        get_incidentes_gateway(), repos, get_settings().reporte_incidentes_limite_por_mes
    )

"""Factories del módulo reporte_incidentes. El gateway SOAP es singleton de
proceso (`lru_cache`): comparte su caché en memoria y su semáforo."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import ArmarReporte
from src.modules.reporte_incidentes.application.use_cases.gestionar_tipificacion import (
    CorregirTipificacion,
    EliminarCategoria,
    GuardarCategoria,
)
from src.modules.reporte_incidentes.application.use_cases.tipificar_pendientes import (
    ConfigIA,
    TipificarPendientes,
)
from src.modules.reporte_incidentes.infrastructure.gemini.gemini_clasificador import (
    GeminiClasificador,
)
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


@lru_cache
def get_clasificador() -> GeminiClasificador:
    s = get_settings()
    return GeminiClasificador(
        s.gemini_api_key,
        (s.reporte_incidentes_gemini_modelo, s.reporte_incidentes_gemini_modelo_fallback),
        (s.reporte_incidentes_gemini_thinking_budget, s.reporte_incidentes_gemini_timeout_segundos),
    )


def _config_ia() -> ConfigIA:
    s = get_settings()
    return ConfigIA(
        lote=s.reporte_incidentes_ia_lote,
        concurrencia=s.reporte_incidentes_ia_concurrencia,
        precio_entrada_por_millon=s.reporte_incidentes_precio_entrada_por_millon,
        precio_salida_por_millon=s.reporte_incidentes_precio_salida_por_millon,
    )


def build_tipificar_pendientes(session: AsyncSession) -> TipificarPendientes:
    dependencias = (SqlAlchemyTipificacionCacheRepository(session), get_clasificador())
    return TipificarPendientes(build_armar_reporte(session), dependencias, _config_ia())


def build_corregir_tipificacion(session: AsyncSession) -> CorregirTipificacion:
    return CorregirTipificacion(
        SqlAlchemyTaxonomiaRepository(session),
        SqlAlchemyTipificacionCacheRepository(session, origen="manual"),
    )


def build_guardar_categoria(session: AsyncSession) -> GuardarCategoria:
    return GuardarCategoria(SqlAlchemyTaxonomiaRepository(session))


def build_eliminar_categoria(session: AsyncSession) -> EliminarCategoria:
    return EliminarCategoria(SqlAlchemyTaxonomiaRepository(session))


def build_taxonomia(session: AsyncSession) -> SqlAlchemyTaxonomiaRepository:
    return SqlAlchemyTaxonomiaRepository(session)

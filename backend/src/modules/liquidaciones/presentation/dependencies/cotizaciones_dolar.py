"""Factory del job `liquidaciones_sync_cotizaciones` (dólar oficial, switch
ARS/USD del detalle de liquidación)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.application.use_cases.sincronizar_cotizaciones_dolar import (
    SincronizarCotizacionesDolar,
    SincronizarCotizacionesDolarPorts,
)
from src.modules.liquidaciones.infrastructure.argentinadatos.httpx_argentinadatos_cotizaciones_client import (  # noqa: E501
    HttpxArgentinaDatosCotizacionesClient,
)
from src.modules.liquidaciones.infrastructure.dolarapi.httpx_dolarapi_client import (
    HttpxDolarApiClient,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_cotizacion_dolar_repository import (  # noqa: E501
    SqlAlchemyCotizacionDolarRepository,
)


def build_sincronizar_cotizaciones_dolar(session: AsyncSession) -> SincronizarCotizacionesDolar:
    return SincronizarCotizacionesDolar(
        SincronizarCotizacionesDolarPorts(
            cotizaciones=SqlAlchemyCotizacionDolarRepository(session),
            historicas=HttpxArgentinaDatosCotizacionesClient(),
            hoy=HttpxDolarApiClient(),
        )
    )

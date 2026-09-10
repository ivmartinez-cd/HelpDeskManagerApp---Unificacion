"""Caso de uso GetLiquidacionDetalle — port de GET /liquidaciones/{id} (más el
detalle de incidentes/alertas/observaciones que el legacy resolvía con relaciones
ORM cargadas perezosamente; acá se piden explícitas). Cada incidente se enriquece
con localidad/SPST/link de Maps de la fila de tabla KM que matchea por (empresa,
sucursal) — el mismo índice que usa el motor de reglas (`_resolucion.py`), para
que la UI nunca muestre un vínculo que el cálculo real no usó (antes indexaba
solo por sucursal y podía "prestar" el SPST de otra empresa con igual sucursal)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.liquidacion_detalle import (
    CotizacionUsdDetalle,
    IncidenteDetalle,
    LiquidacionDetalle,
)
from src.modules.liquidaciones.application.use_cases.sincronizar_cotizaciones_dolar import (
    PERIODO_INICIO,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.cotizacion_dolar_repository import (
    CotizacionDolarRepository,
)
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import (
    TablaKmRepository,
)
from src.modules.liquidaciones.domain.services.motor_reglas._resolucion import (
    indexar_tablas_km,
    resolver_tabla_km,
)


@dataclass(frozen=True)
class GetLiquidacionDetallePorts:
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    alertas: AlertaRepository
    tablas_km: TablaKmRepository
    cotizaciones: CotizacionDolarRepository


class GetLiquidacionDetalle:
    def __init__(self, ports: GetLiquidacionDetallePorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> LiquidacionDetalle:
        liquidacion = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)
        incidentes = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        tabla_km = await self._ports.tablas_km.list_by_prestador(liquidacion.prestador_id)
        indice = indexar_tablas_km(tabla_km)
        return LiquidacionDetalle(
            liquidacion=liquidacion,
            incidentes=[_enriquecer(i, indice) for i in incidentes],
            alertas=await self._ports.alertas.list_by_liquidacion(liquidacion_id),
            cotizacion_usd=await self._cotizacion_usd(liquidacion.periodo),
        )

    async def _cotizacion_usd(self, periodo: str) -> CotizacionUsdDetalle | None:
        if periodo < PERIODO_INICIO:
            return None
        cotizacion = await self._ports.cotizaciones.get_by_periodo(periodo)
        if cotizacion is None:
            return None
        return CotizacionUsdDetalle(compra=cotizacion.compra, venta=cotizacion.venta)


def _enriquecer(
    incidente: Incidente, indice: dict[tuple[str, str], TablaKm]
) -> IncidenteDetalle:
    fila = resolver_tabla_km(incidente, indice)
    return IncidenteDetalle(
        incidente=incidente,
        localidad_cliente=fila.localidad_cliente if fila else None,
        spst_id=fila.spst_id if fila else None,
        url_maps=fila.url_maps if fila else None,
    )

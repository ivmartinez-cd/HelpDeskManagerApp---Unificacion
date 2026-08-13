"""Caso de uso GetLiquidacionDetalle — port de GET /liquidaciones/{id} (más el
detalle de incidentes/alertas/observaciones que el legacy resolvía con relaciones
ORM cargadas perezosamente; acá se piden explícitas). Cada incidente se enriquece
con localidad/SPST/link de Maps de la fila de tabla KM que matchea por sucursal."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.liquidacion_detalle import (
    IncidenteDetalle,
    LiquidacionDetalle,
)
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.alerta_repository import AlertaRepository
from src.modules.liquidaciones.domain.repositories.incidente_repository import (
    IncidenteRepository,
)
from src.modules.liquidaciones.domain.repositories.liquidacion_repository import (
    LiquidacionRepository,
)
from src.modules.liquidaciones.domain.repositories.observacion_repository import (
    ObservacionRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import (
    TablaKmRepository,
)


@dataclass(frozen=True)
class GetLiquidacionDetallePorts:
    liquidaciones: LiquidacionRepository
    incidentes: IncidenteRepository
    alertas: AlertaRepository
    observaciones: ObservacionRepository
    tablas_km: TablaKmRepository


class GetLiquidacionDetalle:
    def __init__(self, ports: GetLiquidacionDetallePorts) -> None:
        self._ports = ports

    async def execute(self, liquidacion_id: UUID) -> LiquidacionDetalle:
        liquidacion = await self._ports.liquidaciones.get_by_id(liquidacion_id)
        if liquidacion is None:
            raise LiquidacionNoEncontradaError(liquidacion_id)
        incidentes = await self._ports.incidentes.list_by_liquidacion(liquidacion_id)
        tabla_km = await self._ports.tablas_km.list_by_prestador(liquidacion.prestador_id)
        por_sucursal = _indexar_por_sucursal(tabla_km)
        return LiquidacionDetalle(
            liquidacion=liquidacion,
            incidentes=[_enriquecer(i, por_sucursal) for i in incidentes],
            alertas=await self._ports.alertas.list_by_liquidacion(liquidacion_id),
            observaciones=await self._ports.observaciones.list_by_liquidacion(liquidacion_id),
        )


def _indexar_por_sucursal(filas: list[TablaKm]) -> dict[str, TablaKm]:
    return {f.sucursal_nombre.strip().lower(): f for f in filas if f.sucursal_nombre}


def _enriquecer(incidente: Incidente, por_sucursal: dict[str, TablaKm]) -> IncidenteDetalle:
    fila = por_sucursal.get((incidente.sucursal_nombre or "").strip().lower())
    return IncidenteDetalle(
        incidente=incidente,
        localidad_cliente=fila.localidad_cliente if fila else None,
        spst_id=fila.spst_id if fila else None,
        url_maps=fila.url_maps if fila else None,
    )

"""Worklist de Tier 0 (Fase 2 del plan de matching + geovalidación): corre el
saneo puro de dominio sobre TODAS las sucursales activas del PST — cero
llamadas a Georef/Nominatim/Google, se puede recalcular en cada request."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.geovalidacion_tier0 import (
    HallazgoTier0,
    Severidad,
    SucursalParaValidar,
    evaluar_tier0,
)

_ORDEN_SEVERIDAD: dict[Severidad, int] = {"alta": 0, "media": 1, "baja": 2}


@dataclass(frozen=True)
class GeovalidacionTier0Ports:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway


@dataclass(frozen=True)
class HallazgoTier0Detalle:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    latitud: float | None
    longitud: float | None
    severidad: Severidad
    codigo: str
    detalle: str


class EvaluarTier0Geovalidacion:
    def __init__(self, ports: GeovalidacionTier0Ports) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[HallazgoTier0Detalle]:
        prestador = await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        por_id = {s.siges_sucursal_id: s for s in sucursales}
        coords_por_id = {
            s.siges_sucursal_id: parse_latlon_siges(s.latitud, s.longitud) for s in sucursales
        }
        base = await self._base_despacho(prestador)
        hallazgos = evaluar_tier0(_a_validar(sucursales, coords_por_id), base=base)
        hallazgos.sort(key=lambda h: _ORDEN_SEVERIDAD[h.severidad])
        return [
            _a_detalle(h, por_id[h.siges_sucursal_id], coords_por_id[h.siges_sucursal_id])
            for h in hallazgos
        ]

    async def _base_despacho(self, prestador: Prestador) -> tuple[float, float] | None:
        if prestador.siges_base_sucursal_id is None:
            return None
        propias = await self._ports.siges.list_sucursales_de_empresa(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        base = next(
            (p for p in propias if p.siges_sucursal_id == prestador.siges_base_sucursal_id), None
        )
        return parse_latlon_siges(base.latitud, base.longitud) if base else None


def _a_validar(
    sucursales: list[SigesSucursalCliente],
    coords_por_id: dict[int, tuple[float, float] | None],
) -> list[SucursalParaValidar]:
    return [
        SucursalParaValidar(
            siges_sucursal_id=s.siges_sucursal_id,
            empresa_nombre=s.empresa_nombre,
            sucursal_nombre=s.sucursal_nombre,
            domicilio=s.domicilio,
            provincia=s.provincia,
            latitud=coords[0] if (coords := coords_por_id[s.siges_sucursal_id]) else None,
            longitud=coords[1] if coords else None,
        )
        for s in sucursales
    ]


def _a_detalle(
    h: HallazgoTier0, sucursal: SigesSucursalCliente, coords: tuple[float, float] | None
) -> HallazgoTier0Detalle:
    return HallazgoTier0Detalle(
        siges_sucursal_id=h.siges_sucursal_id,
        empresa_nombre=sucursal.empresa_nombre,
        sucursal_nombre=sucursal.sucursal_nombre,
        domicilio=sucursal.domicilio,
        latitud=coords[0] if coords else None,
        longitud=coords[1] if coords else None,
        severidad=h.severidad,
        codigo=h.codigo,
        detalle=h.detalle,
    )

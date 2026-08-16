"""Cola de revisión de geocodes: listado con candidatos y resolución humana.

La elección es siempre explícita: un candidato del cache (procedencia
'geocode') o coordenadas pegadas a mano (procedencia 'manual'). Nada se
resuelve "por score" — regla de la Fase 0."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import (
    PROCEDENCIA_GEOCODE,
    PROCEDENCIA_MANUAL,
    SucursalCoordenadas,
)
from src.modules.liquidaciones.domain.errors import SucursalCoordenadasNoEncontradaError
from src.modules.liquidaciones.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.shared.domain.errors import ValidationError

ESTADO_RESUELTA = "resuelta"
ESTADO_AMBIGUA = "ambigua"
ESTADO_SIN_RESULTADOS = "sin_resultados"
ESTADO_SIN_DIRECCION = "sin_direccion"
ESTADO_PENDIENTE = "pendiente"


@dataclass(frozen=True)
class CoordenadasPorts:
    sucursal_coords: SucursalCoordenadasRepository
    geocode_cache: GeocodeCacheRepository


@dataclass(frozen=True)
class SucursalConCandidatos:
    sucursal: SucursalCoordenadas
    estado: str
    candidatos: tuple[GeocodeCandidato, ...]


class ListarCoordenadasPendientes:
    def __init__(self, ports: CoordenadasPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[SucursalConCandidatos]:
        filas = await self._ports.sucursal_coords.list_by_prestador(prestador_id)
        return [await self._con_candidatos(f) for f in filas]

    async def _con_candidatos(self, fila: SucursalCoordenadas) -> SucursalConCandidatos:
        if fila.resuelta:
            return SucursalConCandidatos(fila, ESTADO_RESUELTA, ())
        if fila.direccion_normalizada is None:
            return SucursalConCandidatos(fila, ESTADO_SIN_DIRECCION, ())
        candidatos = await self._ports.geocode_cache.get(fila.direccion_normalizada)
        if candidatos is None:
            return SucursalConCandidatos(fila, ESTADO_PENDIENTE, ())
        if not candidatos:
            return SucursalConCandidatos(fila, ESTADO_SIN_RESULTADOS, ())
        return SucursalConCandidatos(fila, ESTADO_AMBIGUA, tuple(candidatos))


class ResolverCoordenadas:
    def __init__(self, ports: CoordenadasPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        siges_sucursal_id: int,
        *,
        candidato_idx: int | None = None,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> SucursalCoordenadas:
        fila = await self._ports.sucursal_coords.get_by_siges_sucursal_id(siges_sucursal_id)
        if fila is None:
            raise SucursalCoordenadasNoEncontradaError(siges_sucursal_id)
        if candidato_idx is not None:
            return await self._resolver_candidato(fila, candidato_idx)
        if latitud is None or longitud is None:
            raise ValidationError("Indicá un candidato o latitud y longitud manuales.")
        return await self._resolver_manual(fila, latitud, longitud)

    async def _resolver_candidato(
        self, fila: SucursalCoordenadas, idx: int
    ) -> SucursalCoordenadas:
        candidatos = (
            await self._ports.geocode_cache.get(fila.direccion_normalizada)
            if fila.direccion_normalizada
            else None
        )
        if not candidatos or idx < 0 or idx >= len(candidatos):
            raise ValidationError(f"Candidato {idx} inexistente para esta sucursal.")
        elegido = candidatos[idx]
        resuelta = await self._ports.sucursal_coords.resolver(
            fila.siges_sucursal_id,
            latitud=elegido.latitud,
            longitud=elegido.longitud,
            procedencia=PROCEDENCIA_GEOCODE,
            formatted_address=elegido.formatted_address,
        )
        return _o_error(resuelta, fila.siges_sucursal_id)

    async def _resolver_manual(
        self, fila: SucursalCoordenadas, latitud: float, longitud: float
    ) -> SucursalCoordenadas:
        resuelta = await self._ports.sucursal_coords.resolver(
            fila.siges_sucursal_id,
            latitud=latitud,
            longitud=longitud,
            procedencia=PROCEDENCIA_MANUAL,
            formatted_address=None,
        )
        return _o_error(resuelta, fila.siges_sucursal_id)


def _o_error(
    resuelta: SucursalCoordenadas | None, siges_sucursal_id: int
) -> SucursalCoordenadas:
    if resuelta is None:
        raise SucursalCoordenadasNoEncontradaError(siges_sucursal_id)
    return resuelta

"""Tier 1b de geovalidación (Fase 2): segunda opinión de Nominatim, SOLO
sobre las sucursales que Tier 1 (Georef) ya marcó con provincia incompatible
— nunca corre sobre el universo completo del PST. Si Nominatim coincide con
Georef, dos fuentes independientes confirman el problema sin gastar Google."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    GeovalidacionTier1Ports,
    HallazgoTier1,
    ListarHallazgosTier1,
)
from src.modules.liquidaciones.domain.repositories.nominatim_gateway import NominatimGateway
from src.modules.liquidaciones.domain.repositories.nominatim_reverse_cache_repository import (
    NominatimReverseCacheRepository,
)
from src.modules.liquidaciones.domain.services.geovalidacion_tier1 import (
    confirmado_por_dos_fuentes,
)


@dataclass(frozen=True)
class GeovalidacionTier1bPorts:
    tier1: GeovalidacionTier1Ports
    nominatim: NominatimGateway
    nominatim_cache: NominatimReverseCacheRepository


@dataclass(frozen=True)
class ResultadoConsultarNominatim:
    consultadas: int
    ya_en_cache: int
    pendientes_por_tope: int


class ConsultarNominatimPendientes:
    """Recorre los hallazgos de Tier 1 (provincia incompatible según Georef)
    y consulta Nominatim para los que todavía no están en cache — el rate
    limit de 1 req/s lo aplica el propio adapter, acá solo se respeta un tope
    por corrida para no bloquear el request HTTP demasiado tiempo."""

    def __init__(self, ports: GeovalidacionTier1bPorts, tope: int) -> None:
        self._ports = ports
        self._tope = tope

    async def execute(self, prestador_id: UUID) -> ResultadoConsultarNominatim:
        hallazgos = await ListarHallazgosTier1(self._ports.tier1).execute(prestador_id)
        consultadas = ya_en_cache = pendientes = 0
        for h in hallazgos:
            if await self._ports.nominatim_cache.get(h.latitud, h.longitud) is not None:
                ya_en_cache += 1
                continue
            if consultadas >= self._tope:
                pendientes += 1
                continue
            ubicacion = await self._ports.nominatim.reverse(h.latitud, h.longitud)
            await self._ports.nominatim_cache.put(h.latitud, h.longitud, ubicacion)
            consultadas += 1
        return ResultadoConsultarNominatim(consultadas, ya_en_cache, pendientes)


@dataclass(frozen=True)
class HallazgoTier1b:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    provincia_declarada: str | None
    provincia_georef: str
    provincia_nominatim: str
    latitud: float
    longitud: float


class ListarHallazgosTier1b:
    """Read-only: cruza los hallazgos de Tier 1 contra lo ya cacheado de
    Nominatim — solo confirmaciones de dos fuentes independientes."""

    def __init__(self, ports: GeovalidacionTier1bPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[HallazgoTier1b]:
        hallazgos_tier1 = await ListarHallazgosTier1(self._ports.tier1).execute(prestador_id)
        confirmados: list[HallazgoTier1b] = []
        for h in hallazgos_tier1:
            confirmado = await self._confirmar(h)
            if confirmado is not None:
                confirmados.append(confirmado)
        return confirmados

    async def _confirmar(self, h: HallazgoTier1) -> HallazgoTier1b | None:
        cacheado = await self._ports.nominatim_cache.get(h.latitud, h.longitud)
        if cacheado is None or cacheado.ubicacion is None:
            return None
        if not confirmado_por_dos_fuentes(
            h.provincia_declarada, h.provincia_georef, cacheado.ubicacion.provincia_nombre
        ):
            return None
        return HallazgoTier1b(
            siges_sucursal_id=h.siges_sucursal_id,
            empresa_nombre=h.empresa_nombre,
            sucursal_nombre=h.sucursal_nombre,
            provincia_declarada=h.provincia_declarada,
            provincia_georef=h.provincia_georef,
            provincia_nominatim=cacheado.ubicacion.provincia_nombre,
            latitud=h.latitud,
            longitud=h.longitud,
        )

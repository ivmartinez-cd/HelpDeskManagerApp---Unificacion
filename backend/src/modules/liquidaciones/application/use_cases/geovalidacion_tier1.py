"""Tier 1 de geovalidación (Fase 2): reverse geocoding de Georef sobre cada
pin, comparado contra la provincia declarada en Siges. Dos casos de uso
separados a propósito (mismo criterio que AuditarPines/ListarPinesSospechosos
con Google): `ConsultarGeorefReversePendientes` es la única que llama a la
red (cacheada, con tope y pausa); `ListarHallazgosTier1` solo lee cache."""

import asyncio
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.repositories.georef_reverse_cache_repository import (
    GeorefReverseCacheRepository,
)
from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    GeoreferenciacionGateway,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.geovalidacion_tier1 import provincias_compatibles


@dataclass(frozen=True)
class GeovalidacionTier1Ports:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    georef: GeoreferenciacionGateway
    georef_cache: GeorefReverseCacheRepository


@dataclass(frozen=True)
class ResultadoConsultarGeoref:
    consultadas: int
    ya_en_cache: int
    sin_coordenadas: int
    pendientes_por_tope: int


class ConsultarGeorefReversePendientes:
    """Recorre las sucursales activas del PST con pin parseable y consulta
    Georef para las que todavía no están en cache — secuencial, con pausa
    entre llamadas reales (no entre hits de cache)."""

    def __init__(self, ports: GeovalidacionTier1Ports, tope: int, pausa_segundos: float) -> None:
        self._ports = ports
        self._tope = tope
        self._pausa = pausa_segundos

    async def execute(self, prestador_id: UUID) -> ResultadoConsultarGeoref:
        sucursales = await self._sucursales(prestador_id)
        consultadas = ya_en_cache = sin_coordenadas = pendientes = 0
        for s in sucursales:
            coords = parse_latlon_siges(s.latitud, s.longitud)
            if coords is None:
                sin_coordenadas += 1
                continue
            if await self._ports.georef_cache.get(*coords) is not None:
                ya_en_cache += 1
                continue
            if consultadas >= self._tope:
                pendientes += 1
                continue
            if consultadas:
                await asyncio.sleep(self._pausa)
            ubicacion = await self._ports.georef.reverse(*coords)
            await self._ports.georef_cache.put(*coords, ubicacion)
            consultadas += 1
        return ResultadoConsultarGeoref(consultadas, ya_en_cache, sin_coordenadas, pendientes)

    async def _sucursales(self, prestador_id: UUID) -> list[SigesSucursalCliente]:
        prestador = await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        return await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class HallazgoTier1:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    provincia_declarada: str | None
    provincia_georef: str
    latitud: float
    longitud: float


class ListarHallazgosTier1:
    """Read-only: compara la provincia declarada en Siges contra la que
    devolvió Georef para el pin — solo sobre lo que ya está en cache."""

    def __init__(self, ports: GeovalidacionTier1Ports) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> list[HallazgoTier1]:
        prestador = await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        hallazgos: list[HallazgoTier1] = []
        for s in sucursales:
            coords = parse_latlon_siges(s.latitud, s.longitud)
            if coords is None:
                continue
            cacheado = await self._ports.georef_cache.get(*coords)
            if cacheado is None or cacheado.ubicacion is None:
                continue  # sin cachear todavía, o Georef sin cobertura ahí
            if not provincias_compatibles(s.provincia, cacheado.ubicacion.provincia_nombre):
                hallazgos.append(HallazgoTier1(
                    siges_sucursal_id=s.siges_sucursal_id,
                    empresa_nombre=s.empresa_nombre,
                    sucursal_nombre=s.sucursal_nombre,
                    provincia_declarada=s.provincia,
                    provincia_georef=cacheado.ubicacion.provincia_nombre,
                    latitud=coords[0],
                    longitud=coords[1],
                ))
        return hallazgos

"""Auditoría de pines de Siges contra el geocode del domicilio.

Dos pasos separados a propósito (la key es paga): `AuditarPines` geocodifica
los domicilios de sucursales CON pin que aún no están en cache (hasta el tope
por corrida); `ListarPinesSospechosos` solo cruza datos ya cacheados — repetir
el listado no llama a Google. Discrepancia = haversine pin Siges ↔ primer
candidato; sospechoso si supera el umbral calibrado (5 km, muestreo
2026-08-15). El `location_type` acompaña para distinguir "pin roto seguro"
(geocode ROOFTOP) de "geocode rural impreciso" (GEOMETRIC_CENTER de ruta)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    parse_latlon_siges,
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    PROCEDENCIA_GEOCODE,
    armar_direccion,
    es_pin_sospechoso,
    haversine_km,
)
from src.shared.domain.errors import ValidationError
from src.shared.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)
from src.shared.domain.repositories.geocoding_gateway import (
    GeocodeCandidato,
    GeocodingGateway,
)


@dataclass(frozen=True)
class PinesPorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    geocode_cache: GeocodeCacheRepository
    geocoding: GeocodingGateway
    sucursal_coords: SucursalCoordenadasRepository


@dataclass(frozen=True)
class PinSospechoso:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    direccion: str
    latitud_siges: float
    longitud_siges: float
    latitud_geocode: float
    longitud_geocode: float
    formatted_address: str
    location_type: str
    discrepancia_km: float


@dataclass(frozen=True)
class AuditarPinesResultado:
    geocodificadas: int
    ya_en_cache: int
    sin_direccion: int
    pendientes_por_tope: int
    llamadas_google: int


class ListarPinesSospechosos:
    def __init__(self, ports: PinesPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID, solo_ids: frozenset[int] | None = None
    ) -> list[PinSospechoso]:
        sospechosos: list[PinSospechoso] = []
        for sucursal, coords, direccion in await _con_pin(self._ports, prestador_id, solo_ids):
            candidatos = await self._ports.geocode_cache.get(direccion)
            if not candidatos:
                continue
            pin = _evaluar(sucursal, coords, direccion, candidatos[0])
            if pin is not None:
                sospechosos.append(pin)
        sospechosos.sort(key=lambda p: -p.discrepancia_km)
        return sospechosos


class AuditarPines:
    """`solo_ids`, cuando se pasa, acota la corrida a ese subconjunto de
    sucursales — el residuo real de Tier 2 (ver `geovalidacion_worklist.py`),
    en vez de auditar el prestador completo. Sin `solo_ids`, comportamiento
    sin cambios."""

    def __init__(self, ports: PinesPorts, tope_llamadas: int) -> None:
        self._ports = ports
        self._tope = tope_llamadas

    async def execute(
        self, prestador_id: UUID, solo_ids: frozenset[int] | None = None
    ) -> AuditarPinesResultado:
        geocodificadas = ya_en_cache = pendientes = llamadas = 0
        sin_direccion = await self._contar_sin_direccion(prestador_id, solo_ids)
        for _, _, direccion in await _con_pin(self._ports, prestador_id, solo_ids):
            if await self._ports.geocode_cache.get(direccion) is not None:
                ya_en_cache += 1
                continue
            if llamadas >= self._tope:
                pendientes += 1
                continue
            candidatos = await self._ports.geocoding.geocode(direccion)
            llamadas += 1
            await self._ports.geocode_cache.put(direccion, candidatos)
            geocodificadas += 1
        return AuditarPinesResultado(
            geocodificadas=geocodificadas,
            ya_en_cache=ya_en_cache,
            sin_direccion=sin_direccion,
            pendientes_por_tope=pendientes,
            llamadas_google=llamadas,
        )

    async def _contar_sin_direccion(
        self, prestador_id: UUID, solo_ids: frozenset[int] | None
    ) -> int:
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        return sum(
            1
            for s in sucursales
            if (solo_ids is None or s.siges_sucursal_id in solo_ids)
            and parse_latlon_siges(s.latitud, s.longitud) is not None
            and armar_direccion(s.domicilio, s.localidad, s.provincia) is None
        )


async def _con_pin(
    ports: PinesPorts, prestador_id: UUID, solo_ids: frozenset[int] | None = None
) -> list[tuple[SigesSucursalCliente, tuple[float, float], str]]:
    prestador = await validar_prestador_vinculado_siges(ports.prestadores, prestador_id)
    sucursales = await ports.siges.list_sucursales_de_prestador(
        prestador.siges_empresa_id  # type: ignore[arg-type]
    )
    if solo_ids is not None:
        sucursales = [s for s in sucursales if s.siges_sucursal_id in solo_ids]
    resultado = []
    for s in sucursales:
        coords = parse_latlon_siges(s.latitud, s.longitud)
        direccion = armar_direccion(s.domicilio, s.localidad, s.provincia)
        if coords is not None and direccion is not None:
            resultado.append((s, coords, direccion))
    return resultado


def _evaluar(
    sucursal: SigesSucursalCliente,
    coords: tuple[float, float],
    direccion: str,
    candidato: GeocodeCandidato,
) -> PinSospechoso | None:
    discrepancia = haversine_km(
        coords[0], coords[1], candidato.latitud, candidato.longitud
    )
    if not es_pin_sospechoso(discrepancia):
        return None
    return PinSospechoso(
        siges_sucursal_id=sucursal.siges_sucursal_id,
        empresa_nombre=sucursal.empresa_nombre,
        sucursal_nombre=sucursal.sucursal_nombre,
        direccion=direccion,
        latitud_siges=coords[0],
        longitud_siges=coords[1],
        latitud_geocode=candidato.latitud,
        longitud_geocode=candidato.longitud,
        formatted_address=candidato.formatted_address,
        location_type=candidato.location_type,
        discrepancia_km=round(discrepancia, 3),
    )


class CorregirPin:
    """Guarda el geocode de un pin sospechoso como override en
    `sucursal_coordenadas`, reemplazando las coords de Siges en el cálculo."""

    def __init__(self, ports: PinesPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID, siges_sucursal_id: int) -> None:
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        sucursal = next(
            (s for s in sucursales if s.siges_sucursal_id == siges_sucursal_id), None
        )
        if sucursal is None:
            raise ValidationError(f"Sucursal {siges_sucursal_id} no encontrada")
        direccion = armar_direccion(sucursal.domicilio, sucursal.localidad, sucursal.provincia)
        if direccion is None:
            raise ValidationError("La sucursal no tiene dirección para geocodificar")
        candidatos = await self._ports.geocode_cache.get(direccion)
        if not candidatos:
            raise ValidationError("Ejecutá 'Auditar con Google' primero para obtener el geocode")
        candidato = candidatos[0]
        await self._ports.sucursal_coords.upsert_pendiente(
            prestador_id=prestador_id,
            siges_sucursal_id=sucursal.siges_sucursal_id,
            empresa_nombre=sucursal.empresa_nombre,
            sucursal_nombre=sucursal.sucursal_nombre,
            direccion_normalizada=direccion,
        )
        await self._ports.sucursal_coords.resolver(
            siges_sucursal_id=sucursal.siges_sucursal_id,
            latitud=candidato.latitud,
            longitud=candidato.longitud,
            procedencia=PROCEDENCIA_GEOCODE,
            formatted_address=candidato.formatted_address,
        )

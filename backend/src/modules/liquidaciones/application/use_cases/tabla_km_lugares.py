"""Operaciones por fila de Tabla KM: buscar lugar (candidatos de geocode),
fijar coordenadas con procedencia y recalcular km ida+vuelta.

El recálculo por fila es directo (sin preview — decisión Fase 0): son 2
elementos de matrix y el usuario lo pide fila por fila viendo lo que toca.
`umbral_viatico` y `observaciones` de la fila se preservan siempre."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    maps_url_ida_vuelta,
    obtener_coords_base,
    validar_prestador_para_distancias,
)
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import (
    PROCEDENCIA_GEOCODE,
    PROCEDENCIA_MANUAL,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import (
    FilaSinCoordenadasError,
    FilaSinDomicilioError,
    TablaKmNoEncontradaError,
)
from src.modules.liquidaciones.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import (
    GeocodeCandidato,
    GeocodingGateway,
)
from src.modules.liquidaciones.domain.repositories.google_maps_gateway import GoogleMapsGateway
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.geolocalizacion import armar_direccion
from src.shared.domain.errors import ValidationError


@dataclass(frozen=True)
class TablaKmLugaresPorts:
    prestadores: PrestadorRepository
    tabla_km: TablaKmRepository
    siges: SigesCatalogoGateway
    geocode_cache: GeocodeCacheRepository
    geocoding: GeocodingGateway
    google_maps: GoogleMapsGateway


class BuscarLugarFila:
    def __init__(self, ports: TablaKmLugaresPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID) -> list[GeocodeCandidato]:
        fila = await _fila_o_error(self._ports.tabla_km, tabla_km_id)
        direccion = armar_direccion(
            fila.domicilio_cliente, fila.localidad_cliente, fila.provincia_cliente
        )
        if direccion is None:
            raise FilaSinDomicilioError(tabla_km_id)
        cacheados = await self._ports.geocode_cache.get(direccion)
        if cacheados is not None:
            return cacheados
        candidatos = await self._ports.geocoding.geocode(direccion)
        await self._ports.geocode_cache.put(direccion, candidatos)
        return candidatos


class ResolverCoordenadasFila:
    def __init__(self, ports: TablaKmLugaresPorts) -> None:
        self._ports = ports

    async def execute(
        self,
        tabla_km_id: UUID,
        *,
        candidato_idx: int | None = None,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> TablaKm:
        fila = await _fila_o_error(self._ports.tabla_km, tabla_km_id)
        if candidato_idx is not None:
            elegido = await self._candidato(fila, candidato_idx)
            return await self._guardar(
                tabla_km_id, elegido.latitud, elegido.longitud,
                PROCEDENCIA_GEOCODE, elegido.formatted_address,
            )
        if latitud is None or longitud is None:
            raise ValidationError("Indicá un candidato o latitud y longitud manuales.")
        return await self._guardar(tabla_km_id, latitud, longitud, PROCEDENCIA_MANUAL, None)

    async def _candidato(self, fila: TablaKm, idx: int) -> GeocodeCandidato:
        direccion = armar_direccion(
            fila.domicilio_cliente, fila.localidad_cliente, fila.provincia_cliente
        )
        candidatos = await self._ports.geocode_cache.get(direccion) if direccion else None
        if not candidatos or idx < 0 or idx >= len(candidatos):
            raise ValidationError(f"Candidato {idx} inexistente para esta fila.")
        return candidatos[idx]

    async def _guardar(
        self,
        tabla_km_id: UUID,
        latitud: float,
        longitud: float,
        procedencia: str,
        formatted_address: str | None,
    ) -> TablaKm:
        actualizada = await self._ports.tabla_km.set_coordenadas(
            tabla_km_id,
            latitud=latitud,
            longitud=longitud,
            coords_origen=procedencia,
            geocode_formatted_address=formatted_address,
            geocode_fecha=datetime.now(UTC) if formatted_address else None,
        )
        if actualizada is None:
            raise TablaKmNoEncontradaError(tabla_km_id)
        return actualizada


class RecalcularKmFila:
    def __init__(self, ports: TablaKmLugaresPorts) -> None:
        self._ports = ports

    async def execute(self, tabla_km_id: UUID) -> TablaKm:
        fila = await _fila_o_error(self._ports.tabla_km, tabla_km_id)
        if fila.latitud_destino is None or fila.longitud_destino is None:
            raise FilaSinCoordenadasError(tabla_km_id)
        prestador = await validar_prestador_para_distancias(
            self._ports.prestadores, fila.prestador_id
        )
        base = await obtener_coords_base(self._ports.siges, prestador)
        destino = (fila.latitud_destino, fila.longitud_destino)
        tramos = await self._ports.google_maps.distancias_km_ida_vuelta(base, [destino])
        ida, vuelta = tramos[0]
        if ida is None or vuelta is None:
            raise FilaSinCoordenadasError(tabla_km_id)
        return await self._guardar(fila, base, destino, ida, vuelta)

    async def _guardar(
        self,
        fila: TablaKm,
        base: tuple[float, float],
        destino: tuple[float, float],
        ida: float,
        vuelta: float,
    ) -> TablaKm:
        total = round(ida + vuelta, 3)
        aplica = total > fila.umbral_viatico
        actualizada = await self._ports.tabla_km.update_distancias(
            fila.id,
            kms_ida=round(ida, 3),
            kms_vuelta=round(vuelta, 3),
            kms_recorrido=total,
            aplica_viatico=aplica,
            kms_a_facturar=total if aplica else 0.0,
            url_maps=maps_url_ida_vuelta(base, destino),
            latitud_destino=destino[0],
            longitud_destino=destino[1],
            coords_origen=fila.coords_origen or "siges",
        )
        if actualizada is None:
            raise TablaKmNoEncontradaError(fila.id)
        return actualizada


async def _fila_o_error(repo: TablaKmRepository, tabla_km_id: UUID) -> TablaKm:
    fila = await repo.get_by_id(tabla_km_id)
    if fila is None:
        raise TablaKmNoEncontradaError(tabla_km_id)
    return fila

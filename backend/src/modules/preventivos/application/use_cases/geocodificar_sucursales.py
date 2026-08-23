"""Geocodifica sucursales del universo de preventivos sin coordenada
confiable en Siges: bbox inválido (Fase 2), coordenada compartida con otra
sucursal de domicilio distinto, o mismo domicilio con pines que no coinciden
entre sí (Fase 3 — ver domain/services/pines_sospechosos.py). Reusa el
gateway/cache compartidos
(shared/infrastructure/geocoding — misma key paga que liquidaciones); la
elección automática y el armado de dirección son puros
(domain/services/geocoding.py). Ambiguas/sin resultado no se persisten: se
reintentan gratis (vía cache) en la próxima corrida, nunca se pisa una
resolución ya guardada por reintento."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.modules.preventivos.domain.entities.sucursal_coordenadas import (
    GeocodificarResultado,
    SucursalCoordenadas,
    SucursalParaGeocoding,
)
from src.modules.preventivos.domain.repositories.preventivos_query_gateway import (
    PreventivosQueryGateway,
)
from src.modules.preventivos.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.preventivos.domain.services.coordenadas import coordenada_valida
from src.modules.preventivos.domain.services.geocoding import armar_direccion, elegir_automatico
from src.modules.preventivos.domain.services.pines_sospechosos import (
    detectar_domicilios_en_conflicto,
    detectar_pines_compartidos,
)
from src.shared.domain.repositories.geocode_cache_repository import GeocodeCacheRepository
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato, GeocodingGateway


@dataclass(frozen=True, slots=True)
class GeocodificarSucursalesDependencies:
    query_gateway: PreventivosQueryGateway
    sucursal_coordenadas: SucursalCoordenadasRepository
    geocode_cache: GeocodeCacheRepository
    geocoding: GeocodingGateway


class GeocodificarSucursalesUseCase:
    def __init__(self, deps: GeocodificarSucursalesDependencies, tope_llamadas: int) -> None:
        self._deps = deps
        self._tope = tope_llamadas
        self._llamadas = 0

    async def execute(self) -> GeocodificarResultado:
        contadores = {"resueltas": 0, "ambiguas": 0, "sin_resultados": 0, "sin_direccion": 0}
        for sucursal in await self._pendientes():
            if self._llamadas >= self._tope:
                break
            contadores[await self._procesar(sucursal)] += 1
        return GeocodificarResultado(
            resueltas=contadores["resueltas"],
            ambiguas=contadores["ambiguas"],
            sin_resultados=contadores["sin_resultados"],
            sin_direccion=contadores["sin_direccion"],
        )

    async def _pendientes(self) -> list[SucursalParaGeocoding]:
        sucursales = await self._deps.query_gateway.list_sucursales_para_geocoding()
        sospechosos = detectar_pines_compartidos(sucursales) | detectar_domicilios_en_conflicto(
            sucursales
        )
        invalidas = [
            s
            for s in sucursales
            if not coordenada_valida(s.latitud, s.longitud) or s.id_sucursal in sospechosos
        ]
        resueltas = await self._deps.sucursal_coordenadas.list_by_siges_sucursal_ids(
            [s.id_sucursal for s in invalidas]
        )
        return [s for s in invalidas if s.id_sucursal not in resueltas]

    async def _procesar(self, sucursal: SucursalParaGeocoding) -> str:
        direccion = armar_direccion(sucursal.domicilio, sucursal.ciudad, sucursal.provincia)
        if direccion is None:
            return "sin_direccion"
        candidatos = await self._candidatos(direccion)
        if not candidatos:
            return "sin_resultados"
        elegido = elegir_automatico(candidatos)
        if elegido is None:
            return "ambiguas"
        await self._guardar(sucursal.id_sucursal, elegido)
        return "resueltas"

    async def _candidatos(self, direccion: str) -> list[GeocodeCandidato]:
        cacheados = await self._deps.geocode_cache.get(direccion)
        if cacheados is not None:
            return cacheados
        self._llamadas += 1
        candidatos = await self._deps.geocoding.geocode(direccion)
        await self._deps.geocode_cache.put(direccion, candidatos)
        return candidatos

    async def _guardar(self, id_sucursal: int, candidato: GeocodeCandidato) -> None:
        await self._deps.sucursal_coordenadas.upsert(
            SucursalCoordenadas(
                siges_sucursal_id=id_sucursal,
                latitud=candidato.latitud,
                longitud=candidato.longitud,
                formatted_address=candidato.formatted_address,
                fecha_resolucion=datetime.now(UTC),
            )
        )

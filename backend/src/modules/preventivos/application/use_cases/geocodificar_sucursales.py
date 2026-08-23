"""Geocodifica sucursales del universo de preventivos sin coordenada
confiable en Siges: bbox inválido (Fase 2), coordenada compartida con otra
sucursal de domicilio distinto, o mismo domicilio con pines que no coinciden
entre sí (Fase 3 — ver domain/services/pines_sospechosos.py). Reusa el
gateway/cache compartidos
(shared/infrastructure/geocoding — misma key paga que liquidaciones); la
elección automática y el armado de dirección son puros
(domain/services/geocoding.py). Ambiguas/sin resultado no se persisten: se
reintentan gratis (vía cache) en la próxima corrida, nunca se pisa una
resolución ya guardada por reintento.

Reconciliación (2026-08-23): Siges es de solo lectura acá, así que si alguien
corrige una coordenada directamente en Siges, un override viejo (de una
corrección nuestra anterior) la tapa para siempre — ver
domain/services/coordenadas.py:coordenada_reconciliada. Cada corrida también
revisa las sucursales YA overrideadas: si la coordenada actual de Siges cayó
cerca de la que habíamos guardado, asumimos que Siges se puso al día y
soltamos el override.

Excluye a propósito las sucursales que siguen en `sospechosos` (pin
compartido/domicilio en conflicto): un miembro de un grupo con pines en
conflicto puede tener su propio pin cerca del override sin que eso signifique
que Siges se corrigió — solo significa que ESE miembro nunca estuvo tan mal,
pero el grupo (por comparación con otro miembro) sigue sin ser confiable.
Bug real encontrado el 2026-08-23: sin este chequeo, el caso Constituyentes
(3 sucursales del mismo domicilio, una con el pin a 1.35km del resto) soltaba
el override de las otras dos apenas su pin individual quedaba a metros del
valor correcto, aunque el grupo seguía en conflicto.

Referencias geográficas para `elegir_automatico` (2026-08-23): antes de
procesar las pendientes, se arma un mapa (ciudad, provincia) → coordenadas de
sucursales ya confiables (override vigente, o raw de Siges válido si no hay
override) — excluyendo sospechosos, que no son confiables. Cada candidato
único que Google devuelve se valida contra esas referencias (ver
domain/services/geocoding.py) antes de auto-elegirse; sin esto, un candidato
"único y preciso" pero en el partido equivocado (misma calle, otro partido)
se guardaba igual — así se colaron los bugs de Garín/San Justo/Hurlingham/
Escobar/Benavídez encontrados ese día a mano."""

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
from src.modules.preventivos.domain.services.coordenadas import (
    coordenada_reconciliada,
    coordenada_valida,
)
from src.modules.preventivos.domain.services.geocoding import (
    agrupar_referencias_por_ciudad,
    armar_direccion,
    clave_ubicacion,
    elegir_automatico,
)
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
        sucursales = await self._deps.query_gateway.list_sucursales_para_geocoding()
        sospechosos = detectar_pines_compartidos(sucursales) | detectar_domicilios_en_conflicto(
            sucursales
        )
        overrides = await self._deps.sucursal_coordenadas.list_by_siges_sucursal_ids(
            [s.id_sucursal for s in sucursales]
        )
        contadores = await self._procesar_pendientes(sucursales, sospechosos, overrides)
        reconciliadas = await self._reconciliar(sucursales, sospechosos)
        return GeocodificarResultado(
            resueltas=contadores["resueltas"],
            ambiguas=contadores["ambiguas"],
            sin_resultados=contadores["sin_resultados"],
            sin_direccion=contadores["sin_direccion"],
            reconciliadas=reconciliadas,
        )

    async def _procesar_pendientes(
        self,
        sucursales: list[SucursalParaGeocoding],
        sospechosos: set[int],
        overrides: dict[int, SucursalCoordenadas],
    ) -> dict[str, int]:
        contadores = {"resueltas": 0, "ambiguas": 0, "sin_resultados": 0, "sin_direccion": 0}
        referencias_por_ciudad = self._referencias_por_ciudad(sucursales, overrides, sospechosos)
        for sucursal in self._pendientes(sucursales, sospechosos, overrides):
            if self._llamadas >= self._tope:
                break
            contadores[await self._procesar(sucursal, referencias_por_ciudad)] += 1
        return contadores

    def _pendientes(
        self,
        sucursales: list[SucursalParaGeocoding],
        sospechosos: set[int],
        overrides: dict[int, SucursalCoordenadas],
    ) -> list[SucursalParaGeocoding]:
        return [
            s
            for s in sucursales
            if (not coordenada_valida(s.latitud, s.longitud) or s.id_sucursal in sospechosos)
            and s.id_sucursal not in overrides
        ]

    def _referencias_por_ciudad(
        self,
        sucursales: list[SucursalParaGeocoding],
        overrides: dict[int, SucursalCoordenadas],
        sospechosos: set[int],
    ) -> dict[tuple[str, str], list[tuple[float, float]]]:
        candidatas = (s for s in sucursales if s.id_sucursal not in sospechosos)
        entradas = [
            entrada
            for entrada in (
                self._entrada_referencia(s, overrides.get(s.id_sucursal)) for s in candidatas
            )
            if entrada is not None
        ]
        return agrupar_referencias_por_ciudad(entradas)

    def _entrada_referencia(
        self, sucursal: SucursalParaGeocoding, override: SucursalCoordenadas | None
    ) -> tuple[str, str, float, float] | None:
        if override is not None:
            return (sucursal.ciudad, sucursal.provincia, override.latitud, override.longitud)
        if coordenada_valida(sucursal.latitud, sucursal.longitud):
            assert sucursal.latitud is not None and sucursal.longitud is not None
            return (sucursal.ciudad, sucursal.provincia, sucursal.latitud, sucursal.longitud)
        return None

    async def _reconciliar(
        self, sucursales: list[SucursalParaGeocoding], sospechosos: set[int]
    ) -> int:
        overrides = await self._deps.sucursal_coordenadas.list_by_siges_sucursal_ids(
            [s.id_sucursal for s in sucursales]
        )
        reconciliadas = 0
        for sucursal in sucursales:
            override = overrides.get(sucursal.id_sucursal)
            if override is None or sucursal.id_sucursal in sospechosos:
                continue
            if coordenada_reconciliada(
                override.latitud, override.longitud, sucursal.latitud, sucursal.longitud
            ):
                await self._deps.sucursal_coordenadas.delete(sucursal.id_sucursal)
                reconciliadas += 1
        return reconciliadas

    async def _procesar(
        self,
        sucursal: SucursalParaGeocoding,
        referencias_por_ciudad: dict[tuple[str, str], list[tuple[float, float]]],
    ) -> str:
        direccion = armar_direccion(sucursal.domicilio, sucursal.ciudad, sucursal.provincia)
        if direccion is None:
            return "sin_direccion"
        candidatos = await self._candidatos(direccion)
        if not candidatos:
            return "sin_resultados"
        clave = clave_ubicacion(sucursal.ciudad, sucursal.provincia)
        referencias = tuple(referencias_por_ciudad.get(clave, ()))
        elegido = elegir_automatico(candidatos, sucursal.ciudad, referencias)
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

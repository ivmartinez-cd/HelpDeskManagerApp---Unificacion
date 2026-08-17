"""Geocodificación de sucursales cliente SIN coordenadas en Siges.

Solo llena vacíos: una sucursal con pin en Siges o con resolución previa no se
toca. Auto-resuelve únicamente candidatos inequívocos (ver
`geolocalizacion.elegir_automatico`); el resto queda en cola de revisión con
sus candidatos cacheados. Cada dirección se consulta a Google UNA vez (cache
por dirección normalizada, ZERO_RESULTS incluido) y la corrida respeta el tope
de llamadas configurado."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    desde_periodo_hace_meses,
    parse_latlon_siges,
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import (
    GeocodeCandidato,
    GeocodingGateway,
)
from src.modules.liquidaciones.domain.repositories.incidente_repository import IncidenteRepository
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
    elegir_automatico,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    nombres_compatibles,
    normalizar_nombre,
)


@dataclass(frozen=True)
class GeocodificarPorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    sucursal_coords: SucursalCoordenadasRepository
    geocode_cache: GeocodeCacheRepository
    geocoding: GeocodingGateway
    incidentes: IncidenteRepository


@dataclass(frozen=True)
class GeocodificarResultado:
    resueltas_auto: int
    ambiguas: int
    sin_resultados: int
    sin_direccion: int
    ya_resueltas: int
    llamadas_google: int
    pendientes_por_tope: int
    sin_actividad: int


class GeocodificarSucursales:
    def __init__(self, ports: GeocodificarPorts, tope_llamadas: int) -> None:
        self._ports = ports
        self._tope = tope_llamadas

    async def execute(self, prestador_id: UUID) -> GeocodificarResultado:
        prestador = await validar_prestador_vinculado_siges(
            self._ports.prestadores, prestador_id
        )
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        activos_raw = await self._ports.incidentes.empresas_con_actividad_reciente(
            prestador.id, desde_periodo_hace_meses(24)
        )
        activos_norm = {normalizar_nombre(n) for n in activos_raw}
        contador = _Contador()
        for sucursal in sucursales:
            empresa = normalizar_nombre(sucursal.empresa_nombre)
            if empresa not in activos_norm and not any(
                nombres_compatibles(empresa, a) for a in activos_norm
            ):
                contador.sin_actividad += 1
                continue
            if parse_latlon_siges(sucursal.latitud, sucursal.longitud) is not None:
                continue
            await self._procesar(prestador_id, sucursal, contador)
        return contador.resultado()

    async def _procesar(
        self, prestador_id: UUID, sucursal: SigesSucursalCliente, contador: "_Contador"
    ) -> None:
        existente = await self._ports.sucursal_coords.get_by_siges_sucursal_id(
            sucursal.siges_sucursal_id
        )
        if existente is not None and existente.resuelta:
            contador.ya_resueltas += 1
            return
        direccion = armar_direccion(sucursal.domicilio, sucursal.localidad, sucursal.provincia)
        await self._ports.sucursal_coords.upsert_pendiente(
            prestador_id=prestador_id,
            siges_sucursal_id=sucursal.siges_sucursal_id,
            empresa_nombre=sucursal.empresa_nombre,
            sucursal_nombre=sucursal.sucursal_nombre,
            direccion_normalizada=direccion,
        )
        if direccion is None:
            contador.sin_direccion += 1
            return
        candidatos = await self._obtener_candidatos(direccion, contador)
        if candidatos is None:
            return
        await self._clasificar(sucursal.siges_sucursal_id, candidatos, contador)

    async def _obtener_candidatos(
        self, direccion: str, contador: "_Contador"
    ) -> list[GeocodeCandidato] | None:
        """`None` = no se pudo consultar (tope agotado); lista = candidatos."""
        cacheados = await self._ports.geocode_cache.get(direccion)
        if cacheados is not None:
            return cacheados
        if contador.llamadas_google >= self._tope:
            contador.pendientes_por_tope += 1
            return None
        candidatos = await self._ports.geocoding.geocode(direccion)
        contador.llamadas_google += 1
        await self._ports.geocode_cache.put(direccion, candidatos)
        return candidatos

    async def _clasificar(
        self,
        siges_sucursal_id: int,
        candidatos: list[GeocodeCandidato],
        contador: "_Contador",
    ) -> None:
        if not candidatos:
            contador.sin_resultados += 1
            return
        elegido = elegir_automatico(candidatos)
        if elegido is None:
            contador.ambiguas += 1
            return
        await self._ports.sucursal_coords.resolver(
            siges_sucursal_id,
            latitud=elegido.latitud,
            longitud=elegido.longitud,
            procedencia=PROCEDENCIA_GEOCODE,
            formatted_address=elegido.formatted_address,
        )
        contador.resueltas_auto += 1


class _Contador:
    def __init__(self) -> None:
        self.resueltas_auto = 0
        self.ambiguas = 0
        self.sin_resultados = 0
        self.sin_direccion = 0
        self.ya_resueltas = 0
        self.llamadas_google = 0
        self.pendientes_por_tope = 0
        self.sin_actividad = 0

    def resultado(self) -> GeocodificarResultado:
        return GeocodificarResultado(
            resueltas_auto=self.resueltas_auto,
            ambiguas=self.ambiguas,
            sin_resultados=self.sin_resultados,
            sin_direccion=self.sin_direccion,
            ya_resueltas=self.ya_resueltas,
            llamadas_google=self.llamadas_google,
            pendientes_por_tope=self.pendientes_por_tope,
            sin_actividad=self.sin_actividad,
        )

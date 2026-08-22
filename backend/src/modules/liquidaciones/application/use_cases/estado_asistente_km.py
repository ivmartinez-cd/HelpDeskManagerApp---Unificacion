"""Diagnóstico del Asistente de KM: TODO el estado del flujo en una llamada.

Es el "cerebro" del wizard APB: el frontend no decide nada solo — este use case
dice qué falta, qué pasos están bloqueados y cuánto costaría (en llamadas a
Google) cada acción, ANTES de ejecutar nada. Garantía estructural: no recibe
ningún gateway de Google — todo sale de la DB local y de Siges read-only.
Las condiciones faltantes son flags, no excepciones: el wizard las convierte
en pasos bloqueados con acción, no en pantallas de error."""

from dataclasses import dataclass, field
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    desde_periodo_hace_meses,
    es_empresa_activa,
    parse_latlon_siges,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.repositories.incidente_repository import IncidenteRepository
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.repositories.sucursal_coordenadas_repository import (
    SucursalCoordenadasRepository,
)
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    armar_direccion,
    es_pin_sospechoso,
    haversine_km,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import normalizar_nombre
from src.shared.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)


@dataclass(frozen=True)
class EstadoAsistenteKmPorts:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    tabla_km: TablaKmRepository
    sucursal_coords: SucursalCoordenadasRepository
    geocode_cache: GeocodeCacheRepository
    incidentes: IncidenteRepository


@dataclass(frozen=True)
class EstadoAsistenteKm:
    vinculado_siges: bool
    base_configurada: bool = False
    base_con_coordenadas: bool = False
    sucursales_activas: int = 0
    ex_clientes: int = 0
    sucursales_nuevas_por_importar: int = 0
    filas_tabla_km: int = 0
    sin_coordenadas: int = 0
    ambiguas_pendientes: int = 0
    filas_sin_km: int = 0
    no_encontradas_en_siges: int = 0
    pines_sospechosos_cacheados: int = 0
    estimacion_geocodificar: int = 0
    estimacion_distancias: int = 0
    estimacion_auditar_pines: int = 0
    tope_por_corrida: int = 0


@dataclass
class _Contadores:
    activas: int = 0
    ex_clientes: int = 0
    nuevas: int = 0
    sin_coordenadas: int = 0
    destinos_ubicables: int = 0
    pines_cacheados: int = 0
    estim_geocodificar: int = 0
    estim_auditar: int = 0
    claves_siges: set[tuple[str, str]] = field(default_factory=set)


class DiagnosticarAsistenteKm:
    def __init__(self, ports: EstadoAsistenteKmPorts, tope_llamadas: int) -> None:
        self._ports = ports
        self._tope = tope_llamadas

    async def execute(self, prestador_id: UUID) -> EstadoAsistenteKm:
        prestador = await self._ports.prestadores.get_by_id(prestador_id)
        if prestador is None:
            raise PrestadorNoEncontradoError(prestador_id)
        if prestador.siges_empresa_id is None:
            return EstadoAsistenteKm(vinculado_siges=False, tope_por_corrida=self._tope)

        base_ok, base_coords_ok = await self._estado_base(prestador)
        filas = await self._ports.tabla_km.list_by_prestador(prestador_id)
        cargadas = {_clave(f.empresa_nombre, f.sucursal_nombre) for f in filas}
        resoluciones = {
            r.siges_sucursal_id: r
            for r in await self._ports.sucursal_coords.list_by_prestador(prestador_id)
        }
        contadores = await self._recorrer_sucursales(prestador, cargadas, resoluciones)
        return EstadoAsistenteKm(
            vinculado_siges=True,
            base_configurada=base_ok,
            base_con_coordenadas=base_coords_ok,
            sucursales_activas=contadores.activas,
            ex_clientes=contadores.ex_clientes,
            sucursales_nuevas_por_importar=contadores.nuevas,
            filas_tabla_km=len(filas),
            sin_coordenadas=contadores.sin_coordenadas,
            ambiguas_pendientes=await self._contar_ambiguas(resoluciones),
            filas_sin_km=sum(1 for f in filas if f.kms_recorrido <= 0),
            # Una fila con siges_sucursal_id ya no cuenta como "no encontrada"
            # aunque su nombre no matchee textualmente (N0): el vínculo N1/N2/
            # manual del matching de sucursales es más fuerte que el nombre.
            no_encontradas_en_siges=sum(
                1
                for f in filas
                if f.siges_sucursal_id is None
                and _clave(f.empresa_nombre, f.sucursal_nombre) not in contadores.claves_siges
            ),
            pines_sospechosos_cacheados=contadores.pines_cacheados,
            estimacion_geocodificar=contadores.estim_geocodificar,
            estimacion_distancias=2 * contadores.destinos_ubicables,
            estimacion_auditar_pines=contadores.estim_auditar,
            tope_por_corrida=self._tope,
        )

    async def _estado_base(self, prestador: Prestador) -> tuple[bool, bool]:
        if prestador.siges_base_sucursal_id is None:
            return False, False
        propias = await self._ports.siges.list_sucursales_de_empresa(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        base = next(
            (p for p in propias if p.siges_sucursal_id == prestador.siges_base_sucursal_id),
            None,
        )
        if base is None:
            return False, False
        return True, parse_latlon_siges(base.latitud, base.longitud) is not None

    async def _recorrer_sucursales(
        self,
        prestador: Prestador,
        cargadas: set[tuple[str, str]],
        resoluciones: dict[int, SucursalCoordenadas],
    ) -> _Contadores:
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        activos_raw = await self._ports.incidentes.empresas_con_actividad_reciente(
            prestador.id, desde_periodo_hace_meses(24)
        )
        activos_norm = {normalizar_nombre(n) for n in activos_raw}
        contadores = _Contadores()
        for s in sucursales:
            contadores.claves_siges.add(_clave(s.empresa_nombre, s.sucursal_nombre))
            if not es_empresa_activa(s.empresa_nombre, activos_norm):
                contadores.ex_clientes += 1
                continue
            contadores.activas += 1
            if _clave(s.empresa_nombre, s.sucursal_nombre) not in cargadas:
                contadores.nuevas += 1
            await self._clasificar(s, resoluciones.get(s.siges_sucursal_id), contadores)
        return contadores

    async def _clasificar(
        self,
        s: SigesSucursalCliente,
        resolucion: SucursalCoordenadas | None,
        contadores: _Contadores,
    ) -> None:
        """Espeja `_resolver_destino` (resolución resuelta > pin Siges) y la
        auditoría de pines (`ListarPinesSospechosos`/`AuditarPines`)."""
        pin_siges = parse_latlon_siges(s.latitud, s.longitud)
        resuelta = resolucion is not None and resolucion.resuelta
        if resuelta or pin_siges is not None:
            contadores.destinos_ubicables += 1
        else:
            contadores.sin_coordenadas += 1
        direccion = armar_direccion(s.domicilio, s.localidad, s.provincia)
        if direccion is None:
            return
        candidatos = await self._ports.geocode_cache.get(direccion)
        if pin_siges is None:
            if not resuelta and candidatos is None:
                contadores.estim_geocodificar += 1
            return
        if candidatos is None:
            contadores.estim_auditar += 1
        elif candidatos and es_pin_sospechoso(
            haversine_km(*pin_siges, candidatos[0].latitud, candidatos[0].longitud)
        ):
            contadores.pines_cacheados += 1

    async def _contar_ambiguas(
        self, resoluciones: dict[int, SucursalCoordenadas]
    ) -> int:
        """Mismo criterio que `ListarCoordenadasPendientes.ESTADO_AMBIGUA`:
        sin resolver, con dirección y con candidatos cacheados no vacíos."""
        ambiguas = 0
        for r in resoluciones.values():
            if r.resuelta or r.direccion_normalizada is None:
                continue
            candidatos = await self._ports.geocode_cache.get(r.direccion_normalizada)
            if candidatos:
                ambiguas += 1
        return ambiguas


def _clave(empresa: str, sucursal: str) -> tuple[str, str]:
    return (normalizar_nombre(empresa), normalizar_nombre(sucursal))

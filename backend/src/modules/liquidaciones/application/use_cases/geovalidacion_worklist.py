"""Worklist final de geovalidación (Fase 2, cierre): cruza Tier 0 + Tier 1b
ya implementados para calcular el residuo real que ameritaría Tier 2
(Google) — nunca el universo completo del PST. Read-only, cero llamadas a
Google: solo chequea si la dirección de cada candidato ya está en
`geocode_cache` para estimar cuántas llamadas nuevas harían falta."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.use_cases._distancias_comunes import (
    validar_prestador_vinculado_siges,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier0 import (
    EvaluarTier0Geovalidacion,
    HallazgoTier0Detalle,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    ListarHallazgosTier1b,
)
from src.modules.liquidaciones.domain.repositories.geocode_cache_repository import (
    GeocodeCacheRepository,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import PrestadorRepository
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import armar_direccion
from src.modules.liquidaciones.domain.services.geovalidacion_worklist import calcular_residuo


@dataclass(frozen=True)
class WorklistTier2Ports:
    prestadores: PrestadorRepository
    siges: SigesCatalogoGateway
    geocode_cache: GeocodeCacheRepository
    evaluar_tier0: EvaluarTier0Geovalidacion
    listar_tier1b: ListarHallazgosTier1b


@dataclass(frozen=True)
class ItemWorklist:
    siges_sucursal_id: int
    empresa_nombre: str
    sucursal_nombre: str
    domicilio: str | None
    motivos: list[str]
    latitud: float | None
    longitud: float | None


@dataclass(frozen=True)
class ResultadoWorklistTier2:
    certeza_absoluta: list[ItemWorklist]
    requiere_verificacion: list[ItemWorklist]
    estimacion_llamadas_google: int


class CalcularWorklistTier2:
    def __init__(self, ports: WorklistTier2Ports) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID) -> ResultadoWorklistTier2:
        hallazgos_t0 = await self._ports.evaluar_tier0.execute(prestador_id)
        hallazgos_t1b = await self._ports.listar_tier1b.execute(prestador_id)
        confirmados = {h.siges_sucursal_id for h in hallazgos_t1b}
        residuo = calcular_residuo(
            [(h.siges_sucursal_id, h.codigo) for h in hallazgos_t0], confirmados
        )

        certeza = _items_de(hallazgos_t0, residuo.certeza_absoluta)
        candidatos = _items_de(hallazgos_t0, residuo.requiere_verificacion)
        estimacion = await self._estimar_llamadas(prestador_id, residuo.requiere_verificacion)

        return ResultadoWorklistTier2(certeza, candidatos, estimacion)

    async def _estimar_llamadas(self, prestador_id: UUID, candidatos_ids: frozenset[int]) -> int:
        if not candidatos_ids:
            return 0
        prestador = await validar_prestador_vinculado_siges(self._ports.prestadores, prestador_id)
        sucursales = await self._ports.siges.list_sucursales_de_prestador(
            prestador.siges_empresa_id  # type: ignore[arg-type]
        )
        faltan = 0
        for s in sucursales:
            if s.siges_sucursal_id not in candidatos_ids:
                continue
            direccion = armar_direccion(s.domicilio, s.localidad, s.provincia)
            if direccion is not None and await self._ports.geocode_cache.get(direccion) is None:
                faltan += 1
        return faltan


def _items_de(
    hallazgos: list[HallazgoTier0Detalle], ids: frozenset[int]
) -> list[ItemWorklist]:
    motivos_por_id: dict[int, list[str]] = {}
    for h in hallazgos:
        if h.siges_sucursal_id in ids:
            motivos_por_id.setdefault(h.siges_sucursal_id, []).append(h.codigo)
    por_id = {h.siges_sucursal_id: h for h in hallazgos}
    return [
        ItemWorklist(
            sid, por_id[sid].empresa_nombre, por_id[sid].sucursal_nombre,
            por_id[sid].domicilio, motivos, por_id[sid].latitud, por_id[sid].longitud,
        )
        for sid, motivos in motivos_por_id.items()
    ]

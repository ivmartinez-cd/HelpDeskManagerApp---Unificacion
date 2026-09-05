"""Casos de uso del sync de tarifarios y mapeo Siges → SPST (ADR-014).

Política del ADR: el sync crea solo vigencias faltantes por grupo (prestador,
tipo, spst_id) de prestadores vinculados, con toda alta entrando por
`CreateTarifario` (recadenado de vigencias garantizado); una vigencia existente
con costo distinto es conflicto que se reporta sin escribir; las descripciones
de Siges sin mapear a un SPST quedan fuera y se reportan. Dry-run first-class.
"""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.siges_tarifarios import (
    ZonaEstado,
    ZonasSigesResultado,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    SpstNoEncontradoError,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.repositories.tarifario_zona_map_repository import (
    TarifarioZonaMapRepository,
)
from src.modules.liquidaciones.domain.services.sync_tarifarios import (
    planificar_sync_tarifarios,
    proponer_mapeo_spst,
)

GENERICA = "Genérica"


@dataclass(frozen=True)
class SigesTarifariosPorts:
    prestadores: PrestadorRepository
    tarifarios: TarifarioRepository
    spsts: SpstRepository
    zona_maps: TarifarioZonaMapRepository
    siges: SigesCatalogoGateway


_Contexto = tuple[
    list[Prestador],
    list[str],
    dict[int, list[SigesCostoServicio]],
    dict[UUID, dict[str, UUID | None]],
]


async def cargar_contexto(
    ports: SigesTarifariosPorts, prestador_id: UUID | None = None
) -> _Contexto:
    """Prestadores vinculados/sin vínculo + costos de Siges por empresa + mapeo
    descripción→SPST por prestador — insumo común de EstadoZonas y Sync.

    `prestador_id` acota el contexto a un solo prestador (pantalla de tarifarios
    filtrada) — `None` mantiene el agregado de todos los vinculados (ADR-014)."""
    todos = await _filtrar_prestador(ports, prestador_id)
    vinculados = [p for p in todos if p.siges_empresa_id is not None]
    sin_vinculo = [p.nombre_corto for p in todos if p.siges_empresa_id is None]
    costos_por_empresa = await _costos_por_empresa(ports, vinculados)
    mapeos = await _mapeos_por_prestador(ports)
    return vinculados, sin_vinculo, costos_por_empresa, mapeos


async def _filtrar_prestador(
    ports: SigesTarifariosPorts, prestador_id: UUID | None
) -> list[Prestador]:
    todos = await ports.prestadores.list_all()
    if prestador_id is None:
        return todos
    filtrados = [p for p in todos if p.id == prestador_id]
    if not filtrados:
        raise PrestadorNoEncontradoError(prestador_id)
    return filtrados


async def _costos_por_empresa(
    ports: SigesTarifariosPorts, vinculados: list[Prestador]
) -> dict[int, list[SigesCostoServicio]]:
    por_empresa: dict[int, list[SigesCostoServicio]] = {}
    ids = [p.siges_empresa_id for p in vinculados if p.siges_empresa_id is not None]
    for costo in await ports.siges.list_costos_habilitados(ids):
        por_empresa.setdefault(costo.siges_empresa_id, []).append(costo)
    return por_empresa


async def _mapeos_por_prestador(ports: SigesTarifariosPorts) -> dict[UUID, dict[str, UUID | None]]:
    mapeos: dict[UUID, dict[str, UUID | None]] = {}
    for mapa in await ports.zona_maps.list_all():
        mapeos.setdefault(mapa.prestador_id, {})[mapa.descripcion_siges] = mapa.spst_id
    return mapeos


class EstadoZonasSiges:
    """Descripciones de zona detectadas en Siges por prestador vinculado, con su
    SPST mapeado actualmente y una propuesta automática cuando hay match
    inequívoco. La UI arma el combo de SPST disponibles con su propia consulta
    a `GET /spsts?prestadorId=` — no hace falta duplicarlo acá."""

    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports

    async def execute(self, prestador_id: UUID | None = None) -> ZonasSigesResultado:
        vinculados, _, costos_por_empresa, mapeos = await cargar_contexto(self._ports, prestador_id)
        zonas: list[ZonaEstado] = []
        for prestador in vinculados:
            costos = costos_por_empresa.get(prestador.siges_empresa_id or 0, [])
            zonas.extend(await self._zonas_de(prestador, costos, mapeos.get(prestador.id, {})))
        return ZonasSigesResultado(zonas=zonas)

    async def _zonas_de(
        self,
        prestador: Prestador,
        costos: list[SigesCostoServicio],
        mapeo: dict[str, UUID | None],
    ) -> list[ZonaEstado]:
        plan = planificar_sync_tarifarios([], costos, mapeo)
        descripciones = sorted(plan.sin_mapear) + sorted(mapeo)
        if not descripciones:
            return []
        spsts = await self._ports.spsts.list_by_prestador(prestador.id)
        propuestas = proponer_mapeo_spst(sorted(plan.sin_mapear), spsts)
        return [
            ZonaEstado(
                prestador_id=prestador.id,
                prestador=prestador.nombre_corto,
                descripcion_siges=descripcion,
                mapeada=descripcion in mapeo,
                spst_id=mapeo.get(descripcion),
                propuesta_spst_id=propuestas.get(descripcion),
            )
            for descripcion in descripciones
        ]


class MapearZonaSiges:
    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID, *, descripcion_siges: str, spst_id: UUID | None
    ) -> TarifarioZonaMap:
        """`spst_id=None` = mapear a la tarifa genérica (sin SPST específico)."""
        if await self._ports.prestadores.get_by_id(prestador_id) is None:
            raise PrestadorNoEncontradoError(prestador_id)
        if spst_id is not None:
            await self._validar_spst_del_prestador(prestador_id, spst_id)
        return await self._ports.zona_maps.upsert(
            prestador_id=prestador_id,
            descripcion_siges=descripcion_siges.strip(),
            spst_id=spst_id,
        )

    async def _validar_spst_del_prestador(self, prestador_id: UUID, spst_id: UUID) -> None:
        spst = await self._ports.spsts.get_by_id(spst_id)
        if spst is None or spst.prestador_id != prestador_id:
            raise SpstNoEncontradoError(spst_id)

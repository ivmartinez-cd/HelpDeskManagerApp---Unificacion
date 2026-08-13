"""Casos de uso del sync de tarifarios y mapeo de zonas contra Siges (ADR-014).

Política del ADR: el sync crea solo vigencias faltantes por grupo (prestador,
tipo, zona) de prestadores vinculados, con toda alta entrando por
`CreateTarifario` (recadenado de vigencias garantizado); una vigencia existente
con costo distinto es conflicto que se reporta sin escribir; las descripciones
de Siges sin mapeo de zona quedan fuera y se reportan. Dry-run first-class.
"""

from collections import Counter
from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.application.dtos.siges_tarifarios import (
    ConflictoTarifario,
    GrupoTarifasCreadas,
    SyncTarifariosResultado,
    ZonaEstado,
    ZonaSinMapear,
    ZonasSigesResultado,
)
from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCatalogoGateway,
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.repositories.tarifario_zona_map_repository import (
    TarifarioZonaMapRepository,
)
from src.modules.liquidaciones.domain.services.sync_tarifarios import (
    PlanSyncTarifarios,
    planificar_sync_tarifarios,
    proponer_mapeo_zonas,
)


@dataclass(frozen=True)
class SigesTarifariosPorts:
    prestadores: PrestadorRepository
    tarifarios: TarifarioRepository
    zona_maps: TarifarioZonaMapRepository
    siges: SigesCatalogoGateway


_Contexto = tuple[
    list[Prestador],
    list[str],
    dict[int, list[SigesCostoServicio]],
    dict[UUID, dict[str, str | None]],
]


async def _contexto(ports: SigesTarifariosPorts) -> _Contexto:
    """Prestadores vinculados/sin vínculo + costos de Siges por empresa + mapeo
    de zonas por prestador — insumo común de EstadoZonas y Sync."""
    todos = await ports.prestadores.list_all()
    vinculados = [p for p in todos if p.siges_empresa_id is not None]
    sin_vinculo = [p.nombre_corto for p in todos if p.siges_empresa_id is None]

    costos_por_empresa: dict[int, list[SigesCostoServicio]] = {}
    for costo in await ports.siges.list_costos_habilitados(
        [p.siges_empresa_id for p in vinculados if p.siges_empresa_id is not None]
    ):
        costos_por_empresa.setdefault(costo.siges_empresa_id, []).append(costo)

    mapeos: dict[UUID, dict[str, str | None]] = {}
    for mapa in await ports.zona_maps.list_all():
        mapeos.setdefault(mapa.prestador_id, {})[mapa.descripcion_siges] = mapa.zona_local

    return vinculados, sin_vinculo, costos_por_empresa, mapeos


class EstadoZonasSiges:
    """Descripciones de zona detectadas en Siges por prestador vinculado, con su
    mapeo actual y una propuesta automática cuando hay match inequívoco."""

    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports

    async def execute(self) -> ZonasSigesResultado:
        vinculados, _, costos_por_empresa, mapeos = await _contexto(self._ports)
        zonas: list[ZonaEstado] = []
        for prestador in vinculados:
            costos = costos_por_empresa.get(prestador.siges_empresa_id or 0, [])
            zonas.extend(await self._zonas_de(prestador, costos, mapeos.get(prestador.id, {})))
        return ZonasSigesResultado(zonas=zonas)

    async def _zonas_de(
        self,
        prestador: Prestador,
        costos: list[SigesCostoServicio],
        mapeo: dict[str, str | None],
    ) -> list[ZonaEstado]:
        plan = planificar_sync_tarifarios([], costos, mapeo)
        descripciones = sorted(plan.zonas_sin_mapear) + sorted(mapeo)
        if not descripciones:
            return []
        tarifarios = await self._ports.tarifarios.list_by_prestador(prestador.id)
        zonas_locales = sorted({t.zona for t in tarifarios if t.zona})
        propuestas = proponer_mapeo_zonas(sorted(plan.zonas_sin_mapear), zonas_locales)
        return [
            ZonaEstado(
                prestador_id=prestador.id,
                prestador=prestador.nombre_corto,
                descripcion_siges=descripcion,
                mapeada=descripcion in mapeo,
                zona_local=mapeo.get(descripcion),
                propuesta=propuestas.get(descripcion),
                zonas_locales=zonas_locales,
            )
            for descripcion in descripciones
        ]


class MapearZonaSiges:
    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports

    async def execute(
        self, prestador_id: UUID, *, descripcion_siges: str, zona_local: str | None
    ) -> TarifarioZonaMap:
        """`zona_local=None` = mapear a la zona genérica (tarifario sin zona)."""
        if await self._ports.prestadores.get_by_id(prestador_id) is None:
            raise PrestadorNoEncontradoError(prestador_id)
        return await self._ports.zona_maps.upsert(
            prestador_id=prestador_id,
            descripcion_siges=descripcion_siges.strip(),
            zona_local=zona_local.strip() if zona_local is not None else None,
        )


class SyncTarifariosDesdeSiges:
    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports
        self._crear = CreateTarifario(ConfigTarifariosPorts(tarifarios=ports.tarifarios))

    async def execute(self, *, dry_run: bool) -> SyncTarifariosResultado:
        vinculados, sin_vinculo, costos_por_empresa, mapeos = await _contexto(self._ports)
        grupos: list[GrupoTarifasCreadas] = []
        conflictos: list[ConflictoTarifario] = []
        zonas_sin_mapear: list[ZonaSinMapear] = []
        creados = 0
        sin_cambios = 0

        for prestador in vinculados:
            plan = planificar_sync_tarifarios(
                await self._ports.tarifarios.list_by_prestador(prestador.id),
                costos_por_empresa.get(prestador.siges_empresa_id or 0, []),
                mapeos.get(prestador.id, {}),
            )
            if not dry_run:
                await self._crear_faltantes(prestador.id, plan)
            creados += len(plan.a_crear)
            sin_cambios += plan.sin_cambios
            self._agregar(prestador.nombre_corto, plan, grupos, conflictos, zonas_sin_mapear)

        return SyncTarifariosResultado(
            dry_run=dry_run,
            creados=creados,
            grupos_creados=grupos,
            conflictos=conflictos,
            sin_cambios=sin_cambios,
            zonas_sin_mapear=zonas_sin_mapear,
            prestadores_sin_vinculo=sin_vinculo,
        )

    async def _crear_faltantes(self, prestador_id: UUID, plan: PlanSyncTarifarios) -> None:
        for candidata in plan.a_crear:
            await self._crear.execute(
                prestador_id=prestador_id,
                tipo_servicio=candidata.tipo_servicio,
                zona=candidata.zona,
                costo_servicio=candidata.costo_servicio,
                costo_km=candidata.costo_km,
                vigencia_desde=candidata.vigencia_desde,
                vigencia_hasta=None,
            )

    def _agregar(
        self,
        prestador: str,
        plan: PlanSyncTarifarios,
        grupos: list[GrupoTarifasCreadas],
        conflictos: list[ConflictoTarifario],
        zonas_sin_mapear: list[ZonaSinMapear],
    ) -> None:
        por_grupo = Counter((c.tipo_servicio, c.zona) for c in plan.a_crear)
        grupos.extend(
            GrupoTarifasCreadas(prestador, tipo, zona, cantidad)
            for (tipo, zona), cantidad in sorted(por_grupo.items(), key=str)
        )
        conflictos.extend(
            ConflictoTarifario(
                prestador=prestador,
                tipo_servicio=c.tipo_servicio,
                zona=c.zona,
                vigencia_desde=c.vigencia_desde,
                campo=c.campo,
                valor_local=c.valor_local,
                valor_siges=c.valor_siges,
            )
            for c in plan.conflictos
        )
        zonas_sin_mapear.extend(
            ZonaSinMapear(prestador, descripcion, filas)
            for descripcion, filas in sorted(plan.zonas_sin_mapear.items())
        )

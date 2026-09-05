"""SyncTarifariosDesdeSiges — dataset 2 de ADR-014: crea las vigencias de
tarifario que faltan localmente a partir de `dbo.CostoServicio` de Siges.

Política del ADR: solo vigencias faltantes por grupo (prestador, tipo, spst_id)
de prestadores vinculados, con toda alta entrando por `CreateTarifario`
(recadenado de vigencias garantizado); una vigencia existente con costo
distinto es conflicto que se reporta sin escribir; las descripciones de Siges
sin mapear a un SPST quedan fuera y se reportan. Dry-run first-class.

Reporta además los prestadores que quedan sin ninguna tarifa genérica
(`prestadores_sin_generica`): sin ella, toda sucursal de Tabla KM sin SPST
vinculado queda sin precio (ALT008 en cada incidente) — caso INFOMAC
2026-09-04, donde la zona de la sede se había mapeado a un SPST en vez de a
Genérica. Separado de `siges_tarifarios.py` (estado de zonas y mapeo) por el
límite de tamaño de archivo (§4)."""

from collections import Counter
from dataclasses import dataclass, field
from uuid import UUID

from src.modules.liquidaciones.application.dtos.siges_tarifarios import (
    ConflictoTarifario,
    GrupoTarifasCreadas,
    SyncTarifariosResultado,
    ZonaSinMapear,
)
from src.modules.liquidaciones.application.use_cases.config_tarifarios import (
    ConfigTarifariosPorts,
    CreateTarifario,
)
from src.modules.liquidaciones.application.use_cases.siges_tarifarios import (
    GENERICA,
    SigesTarifariosPorts,
    cargar_contexto,
)
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
)
from src.modules.liquidaciones.domain.services.sync_tarifarios import (
    ConflictoTarifa,
    PlanSyncTarifarios,
    planificar_sync_tarifarios,
)


@dataclass
class _Acumulado:
    """Totales del sync a lo largo de los prestadores vinculados."""

    creados: int = 0
    sin_cambios: int = 0
    grupos: list[GrupoTarifasCreadas] = field(default_factory=list)
    conflictos: list[ConflictoTarifario] = field(default_factory=list)
    zonas_sin_mapear: list[ZonaSinMapear] = field(default_factory=list)
    sin_generica: list[str] = field(default_factory=list)

    def resultado(
        self, *, dry_run: bool, prestadores_sin_vinculo: list[str]
    ) -> SyncTarifariosResultado:
        return SyncTarifariosResultado(
            dry_run=dry_run,
            creados=self.creados,
            grupos_creados=self.grupos,
            conflictos=self.conflictos,
            sin_cambios=self.sin_cambios,
            zonas_sin_mapear=self.zonas_sin_mapear,
            prestadores_sin_vinculo=prestadores_sin_vinculo,
            prestadores_sin_generica=self.sin_generica,
        )


def _tiene_generica(existentes: list[Tarifario], plan: PlanSyncTarifarios) -> bool:
    """Lo ya cargado más lo que este mismo sync va a crear."""
    return any(t.spst_id is None for t in existentes) or any(
        c.spst_id is None for c in plan.a_crear
    )


class SyncTarifariosDesdeSiges:
    def __init__(self, ports: SigesTarifariosPorts) -> None:
        self._ports = ports
        self._crear = CreateTarifario(ConfigTarifariosPorts(tarifarios=ports.tarifarios))

    async def execute(
        self, *, dry_run: bool, prestador_id: UUID | None = None
    ) -> SyncTarifariosResultado:
        vinculados, sin_vinculo, costos_por_empresa, mapeos = await cargar_contexto(
            self._ports, prestador_id
        )
        acum = _Acumulado()
        for prestador in vinculados:
            costos = costos_por_empresa.get(prestador.siges_empresa_id or 0, [])
            mapeo = mapeos.get(prestador.id, {})
            await self._sincronizar_prestador(prestador, costos, mapeo, dry_run, acum)
        return acum.resultado(dry_run=dry_run, prestadores_sin_vinculo=sin_vinculo)

    async def _sincronizar_prestador(
        self,
        prestador: Prestador,
        costos: list[SigesCostoServicio],
        mapeo: dict[str, UUID | None],
        dry_run: bool,
        acum: _Acumulado,
    ) -> None:
        existentes = await self._ports.tarifarios.list_by_prestador(prestador.id)
        plan = planificar_sync_tarifarios(existentes, costos, mapeo)
        if not dry_run:
            await self._crear_faltantes(prestador.id, plan)
        acum.creados += len(plan.a_crear)
        acum.sin_cambios += plan.sin_cambios
        spsts = await self._ports.spsts.list_by_prestador(prestador.id)
        nombres = {s.id: s.nombre for s in spsts}
        _agregar_resumen(prestador.nombre_corto, plan, nombres, acum)
        if not _tiene_generica(existentes, plan):
            acum.sin_generica.append(prestador.nombre_corto)

    async def _crear_faltantes(self, prestador_id: UUID, plan: PlanSyncTarifarios) -> None:
        for candidata in plan.a_crear:
            await self._crear.execute(
                prestador_id=prestador_id,
                tipo_servicio=candidata.tipo_servicio,
                spst_id=candidata.spst_id,
                costo_servicio=candidata.costo_servicio,
                costo_km=candidata.costo_km,
                vigencia_desde=candidata.vigencia_desde,
                vigencia_hasta=None,
            )


def _agregar_resumen(
    prestador: str, plan: PlanSyncTarifarios, nombres_spst: dict[UUID, str], acum: _Acumulado
) -> None:
    def nombre_de(spst_id: UUID | None) -> str:
        return nombres_spst.get(spst_id, "?") if spst_id else GENERICA

    por_grupo = Counter((c.tipo_servicio, c.spst_id) for c in plan.a_crear)
    acum.grupos.extend(
        GrupoTarifasCreadas(prestador, tipo, nombre_de(spst_id), cantidad)
        for (tipo, spst_id), cantidad in sorted(por_grupo.items(), key=str)
    )
    acum.conflictos.extend(_conflicto(prestador, c, nombre_de(c.spst_id)) for c in plan.conflictos)
    acum.zonas_sin_mapear.extend(
        ZonaSinMapear(prestador, descripcion, filas)
        for descripcion, filas in sorted(plan.sin_mapear.items())
    )


def _conflicto(prestador: str, c: ConflictoTarifa, spst_nombre: str) -> ConflictoTarifario:
    return ConflictoTarifario(
        prestador=prestador,
        tipo_servicio=c.tipo_servicio,
        spst_nombre=spst_nombre,
        vigencia_desde=c.vigencia_desde,
        campo=c.campo,
        valor_local=c.valor_local,
        valor_siges=c.valor_siges,
    )

"""Arma el tablero de la herramienta Proyección — el mismo pipeline para el
proceso real de Siges (`get_tablero_proyeccion_siges.py`) que para los datos
de ejemplo: cada fila es el cálculo del motor o, si el operador ya decidió
algo sobre esa fila en ESE proceso, su decisión restaurada como en el legacy
(`GrillaEstimacion.RestaurarOverridesAsync`, ver
`_resolver_resultado_final.py`)."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.decision_operador_dto import (
    DecisionOperadorDto,
    SolicitudRestauracionDto,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.fila_proyeccion_dto import FilaProyeccionDto
from src.modules.contadores.application.dtos.parque_historico_dto import (
    parque_historico_de_ejemplo,
)
from src.modules.contadores.application.dtos.resumen_proyeccion_dto import (
    RestauracionDecisionesDto,
    ResumenProyeccionDto,
)
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    ReleerLecturas as ReleerLecturas,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    con_pls_releidas,
)
from src.modules.contadores.application.use_cases._releer_pl_manual import (
    releer_lecturas_de_siges as releer_lecturas_de_siges,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    EstadoDecision,
    FilaResuelta,
    decisiones_no_descartadas,
    es_fuente_pendiente,
    resolver_resultado_final,
)
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    equipos_ejemplo,
)

_Decisiones = dict[tuple[int, str], DecisionOperadorDto]

# El BarChart del legacy: 11 meses de historia (H11..H01) + el período actual.
_MESES_HISTORIA = 11


@dataclass(frozen=True, slots=True)
class TableroProyeccionResult:
    filas: list[FilaProyeccionDto]
    resumen: ResumenProyeccionDto
    restauracion: RestauracionDecisionesDto = field(default_factory=RestauracionDecisionesDto)


class GetTableroProyeccionUseCase:
    """`obtener_equipos` desacopla la fuente de datos (ejemplo vs. SiGes
    real, MODELO_DE_DATOS.md §3.4). Sin `restauracion` en `execute` no se
    restaura ninguna decisión. `releer_lecturas` (opcional, ver
    `releer_lecturas_de_siges`) vuelve a pedir a Siges las lecturas de una
    P/L manual por `ID_Contador`, como `ReconstruirOverrideAsync`; sin él se
    usan las que quedaron guardadas con la decisión."""

    def __init__(
        self,
        decisiones: DecisionesOperadorPort,
        obtener_equipos: Callable[[], list[EquipoProceso]] = equipos_ejemplo,
        releer_lecturas: ReleerLecturas | None = None,
    ) -> None:
        self._decisiones = decisiones
        self._obtener_equipos = obtener_equipos
        self._releer_lecturas = releer_lecturas

    async def execute(
        self, ctx: ContextoProcesoDto, restauracion: SolicitudRestauracionDto | None = None
    ) -> TableroProyeccionResult:
        vigentes, hasta = await self._decisiones_de(restauracion)
        calculadas = [
            _calcular(_ClaseEnProceso(equipo, clase, ctx), vigentes)
            for equipo in self._obtener_equipos()
            for clase in equipo.clases
        ]
        filas = [c.fila for c in calculadas]
        restauracion_resumen = _restauracion_de(calculadas, hasta)
        return TableroProyeccionResult(filas, _resumen_de(filas), restauracion_resumen)

    async def _decisiones_de(
        self, restauracion: SolicitudRestauracionDto | None
    ) -> tuple[_Decisiones, datetime | None]:
        """Una sola consulta para todo el tablero (no una por fila)."""
        if restauracion is None:
            return {}, None
        todas = await self._decisiones.listar_por_proceso(restauracion.nro_proceso)
        vigentes = decisiones_no_descartadas(todas, restauracion.descartar_hasta)
        fechas = [d.actualizado_en for d in todas.values() if d.actualizado_en is not None]
        return await self._con_lecturas_releidas(vigentes), max(fechas, default=None)

    async def _con_lecturas_releidas(self, decisiones: _Decisiones) -> _Decisiones:
        releer = self._releer_lecturas
        if releer is None:
            return decisiones
        return await con_pls_releidas(decisiones, releer)


@dataclass(frozen=True, slots=True)
class _ClaseEnProceso:
    equipo: EquipoProceso
    clase: ClaseProceso
    ctx: ContextoProcesoDto


@dataclass(frozen=True, slots=True)
class _FilaCalculada:
    fila: FilaProyeccionDto
    estado_decision: EstadoDecision


def _calcular(item: _ClaseEnProceso, decisiones: _Decisiones) -> _FilaCalculada:
    decision = decisiones.get((item.equipo.id_maquina, item.clase.clase))
    entrada = construir_estimacion_input(item.equipo, item.clase, item.ctx)
    resuelta = resolver_resultado_final(entrada, decision)
    campos = {
        **_campos_equipo(item.equipo),
        **_campos_clase(item.clase, resuelta, item.ctx.fecha_objetivo),
        **_campos_resultado(item.clase, resuelta),
        **_campos_marcadores(resuelta),
        **_campos_referencias(item.clase),
    }
    return _FilaCalculada(FilaProyeccionDto(**campos), resuelta.estado_decision)


def _campos_equipo(equipo: EquipoProceso) -> dict[str, Any]:
    return dict(
        id_maquina=equipo.id_maquina,
        nro_serie=equipo.nro_serie,
        empresa=equipo.empresa,
        sucursal=equipo.sucursal,
        sector=equipo.sector,
        modelo=equipo.modelo,
        estado_maquina=equipo.estado_maquina,
        estado_maquina_desc=equipo.estado_maquina_desc,
        empresa_actual_desc=equipo.empresa_actual_desc,
        id_art_gen=equipo.id_art_gen,
        id_modo_oper=equipo.id_modo_oper,
    )


def _campos_clase(
    clase: ClaseProceso, resuelta: FilaResuelta, fecha_objetivo: date
) -> dict[str, Any]:
    anterior = clase.ultimo_contador_facturado
    return dict(
        tecnologia=clase.tecnologia,
        clase=clase.clase,
        meses_sin_real=_meses_sin_real(clase, fecha_objetivo),
        historico_12=_historico_con_actual(clase.historico_12, resuelta.resultado.impresiones),
        prom_6_facturados=clase.prom_6_facturados,
        ultimo_facturado_valor=anterior.valor if anterior else None,
        ultimo_facturado_fecha=anterior.fecha if anterior else None,
        ultimo_facturado_tipo=anterior.tipo_toma if anterior else None,
        es_real=clase.ya_real,
        es_clase_sintetica=clase.es_clase_sintetica,
    )


def _campos_resultado(clase: ClaseProceso, resuelta: FilaResuelta) -> dict[str, Any]:
    r = resuelta.resultado
    return dict(
        estim_propuesto=clase.valor_real_cargado if clase.ya_real else r.estim_propuesto,
        tipo_toma=clase.tipo_toma_actual if clase.ya_real else r.tipo_toma,
        fecha_toma_actual=clase.fecha_toma_actual if clase.ya_real else None,
        impresiones=r.impresiones,
        fuente=r.fuente,
        metodo_detalle=r.metodo_detalle,
        detalle_calculo=r.detalle_calculo,
        detalle_parque=r.detalle_parque,
        dias_par_pl=r.dias_par_pl,
        tasa_diaria=r.tasa_diaria,
        dias_proyectados=r.dias_proyectados,
        metodo=r.metodo,
        etiqueta_nivel=r.etiqueta_nivel,
        guia_operador=r.nota_operador,
        editado_por_operador=resuelta.estado_decision == "restaurada",
    )


def _campos_marcadores(resuelta: FilaResuelta) -> dict[str, Any]:
    """Semáforo, colores y bordes de la celda (`AplicarMarcadores`)."""
    r = resuelta.resultado
    return dict(
        coloreo=r.coloreo,
        borde_salto_imposible=r.borde_salto_imposible,
        semaforo=r.semaforo,
        requiere_confirmacion=r.requiere_confirmacion,
        t4_sin_revisar=r.t4_sin_revisar,
        meses_sin_real_en_alerta=r.meses_sin_real_en_alerta,
    )


def _campos_referencias(clase: ClaseProceso) -> dict[str, Any]:
    """Lecturas para preseleccionar L/P en el panel y parques por nivel."""
    ur, ra = clase.ultimo_real, clase.real_anterior
    return dict(
        ultimo_real_fecha=ur.fecha if ur else None,
        ultimo_real_tipo=ur.tipo_toma if ur else None,
        real_anterior_fecha=ra.fecha if ra else None,
        real_anterior_tipo=ra.tipo_toma if ra else None,
        parque_historico=clase.parque_historico or parque_historico_de_ejemplo(clase),
    )


def _historico_con_actual(
    historico: tuple[float, ...], impresiones: float | None
) -> tuple[float, ...]:
    """11 meses de historia (viejo → reciente) + el período actual al final,
    con el resultado ya calculado (real o estimado; 0 si no hay) — el slot
    del mes actual que traiga la fuente de datos es solo un lugar reservado."""
    if not historico:
        return historico
    return (*historico[:_MESES_HISTORIA], impresiones if impresiones is not None else 0.0)


def _meses_sin_real(clase: ClaseProceso, fecha_objetivo: date) -> int | None:
    if clase.ultimo_real is None:
        return None
    return meses_entre(clase.ultimo_real.fecha, fecha_objetivo)


def _resumen_de(filas: list[FilaProyeccionDto]) -> ResumenProyeccionDto:
    """`GrillaEstimacion` del legacy: estimados = a estimar sin pendientes;
    total = máquinas distintas (un Mono+Color aporta 2 filas, 1 máquina)."""
    a_estimar = [f for f in filas if not f.es_real]
    pendientes = sum(1 for f in a_estimar if es_fuente_pendiente(f.fuente))
    return ResumenProyeccionDto(
        reales=len(filas) - len(a_estimar),
        estimados=len(a_estimar) - pendientes,
        pendientes=pendientes,
        sospechosos=sum(1 for f in filas if f.borde_salto_imposible),
        total=len({f.id_maquina for f in filas}),
    )


def _restauracion_de(
    calculadas: list[_FilaCalculada], vigentes_hasta: datetime | None
) -> RestauracionDecisionesDto:
    return RestauracionDecisionesDto(
        restauradas=sum(1 for c in calculadas if c.estado_decision == "restaurada"),
        descartadas=sum(1 for c in calculadas if c.estado_decision == "descartada"),
        vigentes_hasta=vigentes_hasta,
    )

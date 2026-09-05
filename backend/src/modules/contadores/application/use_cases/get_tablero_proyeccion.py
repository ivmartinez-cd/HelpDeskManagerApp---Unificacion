"""Arma el tablero de la herramienta Proyección. Usa datos de ejemplo
(`infrastructure/ejemplo/datos_ejemplo_proyeccion.py`) mientras no se resuelve
el acceso real a SiGes — ver la nota de seguridad de MIGRACION_SISTEMAS.md
(credencial `SiGesReadOnly` pendiente de rotación). El motor de estimación
(`domain/services/estimacion/motor.py`) corre igual que correría con datos
reales: reemplazar la fuente de equipos es el único cambio necesario el día
que se conecte a SiGes."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from typing import Any

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.decision_operador_dto import DecisionOperadorDto
from src.modules.contadores.application.dtos.equipo_proceso_dto import (
    ClaseProceso,
    EquipoProceso,
)
from src.modules.contadores.application.dtos.fila_proyeccion_dto import FilaProyeccionDto
from src.modules.contadores.application.dtos.resumen_proyeccion_dto import ResumenProyeccionDto
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._resolver_resultado_final import (
    resolver_resultado_final,
)
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.services.estimacion.antiguedad import meses_entre
from src.modules.contadores.domain.services.estimacion.motor import estimar
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.infrastructure.ejemplo.datos_ejemplo_proyeccion import (
    equipos_ejemplo,
)


@dataclass(frozen=True, slots=True)
class TableroProyeccionResult:
    filas: list[FilaProyeccionDto]
    resumen: ResumenProyeccionDto


class GetTableroProyeccionUseCase:
    """`obtener_equipos` desacopla la fuente de datos (ejemplo vs. SiGes
    real, MODELO_DE_DATOS.md §3.4) — default a `equipos_ejemplo` para no
    romper al resto del pipeline, que no distingue entre ambas fuentes."""

    def __init__(
        self,
        decisiones: DecisionesOperadorPort,
        obtener_equipos: Callable[[], list[EquipoProceso]] = equipos_ejemplo,
    ) -> None:
        self._decisiones = decisiones
        self._obtener_equipos = obtener_equipos

    async def execute(self, ctx: ContextoProcesoDto) -> TableroProyeccionResult:
        # Una sola consulta para todo el tablero (no una por fila) — ver
        # docstring de DecisionesOperadorPort.listar_todas.
        contexto = _ContextoArmado(ctx, await self._decisiones.listar_todas())
        filas = [
            self._fila_de(equipo, clase, contexto)
            for equipo in self._obtener_equipos()
            for clase in equipo.clases
        ]
        return TableroProyeccionResult(filas, _resumen_de(filas))

    def _fila_de(
        self, equipo: EquipoProceso, clase: ClaseProceso, contexto: "_ContextoArmado"
    ) -> FilaProyeccionDto:
        entrada = construir_estimacion_input(equipo, clase, contexto.ctx)
        automatico = estimar(entrada)
        decision = contexto.decisiones.get((equipo.id_maquina, clase.clase))
        resultado = resolver_resultado_final(clase, automatico, decision)
        calculo = _CalculoClase(equipo, clase, resultado, decision)
        return _armar_fila(calculo, contexto.ctx.fecha_objetivo)


@dataclass(frozen=True, slots=True)
class _ContextoArmado:
    ctx: ContextoProcesoDto
    decisiones: dict[tuple[int, str], DecisionOperadorDto]


@dataclass(frozen=True, slots=True)
class _CalculoClase:
    equipo: EquipoProceso
    clase: ClaseProceso
    resultado: EstimacionResultado
    decision: DecisionOperadorDto | None


def _armar_fila(calculo: _CalculoClase, fecha_objetivo: date) -> FilaProyeccionDto:
    return FilaProyeccionDto(
        **_campos_identidad(calculo, fecha_objetivo), **_campos_calculo(calculo)
    )


def _historico_con_actual(
    historico: tuple[float, ...], impresiones: float | None
) -> tuple[float, ...]:
    """El último punto del histórico es el mes actual: se completa con el
    resultado ya calculado (impresiones reales o estimadas), no con lo que
    haya traído la fuente de datos para ese slot."""
    if not historico:
        return historico
    return (*historico[:-1], impresiones if impresiones is not None else 0.0)


def _campos_identidad(calculo: _CalculoClase, fecha_objetivo: date) -> dict[str, Any]:
    campos_clase = _campos_clase(calculo, fecha_objetivo)
    return {**_campos_equipo(calculo.equipo), **campos_clase}


def _campos_equipo(equipo: EquipoProceso) -> dict[str, Any]:
    return dict(
        id_maquina=equipo.id_maquina,
        nro_serie=equipo.nro_serie,
        empresa=equipo.empresa,
        sucursal=equipo.sucursal,
        sector=equipo.sector,
        modelo=equipo.modelo,
        estado_maquina=equipo.estado_maquina,
    )


def _campos_clase(calculo: _CalculoClase, fecha_objetivo: date) -> dict[str, Any]:
    clase = calculo.clase
    return dict(
        tecnologia=clase.tecnologia,
        clase=clase.clase,
        meses_sin_real=_meses_sin_real(clase, fecha_objetivo),
        historico_12=_historico_con_actual(clase.historico_12, calculo.resultado.impresiones),
        prom_6_facturados=clase.prom_6_facturados,
        ultimo_facturado_valor=clase.ultimo_contador_facturado.valor,
        ultimo_facturado_fecha=clase.ultimo_contador_facturado.fecha,
        ultimo_facturado_tipo=clase.ultimo_contador_facturado.tipo_toma,
        es_real=clase.ya_real,
        es_clase_sintetica=clase.es_clase_sintetica,
    )


def _campos_calculo(calculo: _CalculoClase) -> dict[str, Any]:
    resultado = calculo.resultado
    return dict(
        estim_propuesto=resultado.estim_propuesto,
        tipo_toma=resultado.tipo_toma,
        impresiones=resultado.impresiones,
        fuente=resultado.fuente,
        metodo_detalle=resultado.metodo_detalle,
        coloreo=resultado.coloreo,
        borde_salto_imposible=resultado.borde_salto_imposible,
        semaforo=resultado.semaforo,
        requiere_confirmacion=resultado.requiere_confirmacion,
        nota_operador=calculo.decision.nota if calculo.decision else None,
    )


def _meses_sin_real(clase: ClaseProceso, fecha_objetivo: date) -> int | None:
    if clase.ultimo_real is None:
        return None
    return meses_entre(clase.ultimo_real.fecha, fecha_objetivo)


def _resumen_de(filas: list[FilaProyeccionDto]) -> ResumenProyeccionDto:
    reales = sum(1 for f in filas if f.es_real)
    pendientes = sum(1 for f in filas if f.fuente == "Pendiente")
    sospechosos = sum(1 for f in filas if f.borde_salto_imposible)
    estimados = len(filas) - reales
    return ResumenProyeccionDto(
        reales=reales,
        estimados=estimados,
        pendientes=pendientes,
        sospechosos=sospechosos,
        total=len(filas),
    )

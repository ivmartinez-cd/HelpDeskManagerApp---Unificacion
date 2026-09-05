from dataclasses import dataclass

from src.modules.contadores.domain.services.estimacion.recesos import (
    dias_activos,
    dias_receso_en_tramo,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef


@dataclass(frozen=True, slots=True)
class ResultadoReglaDeTres:
    """Regla de tres Partida→Llegada→fecha objetivo (REGLAS_DE_NEGOCIO §5.2).
    `dias_proyectados` puede ser negativo: Llegada posterior a la fecha
    objetivo interpola el estimado hacia atrás, por debajo de la Llegada."""

    estimado: float
    impresiones: float
    dias_par: int
    dias_proyectados: int
    dias_receso_descontados: int
    tasa_diaria: float


@dataclass(frozen=True, slots=True)
class _Tramo:
    dias_par: int
    dias_proyectados: int


def calcular_regla_de_tres(
    partida: LecturaRef, llegada: LecturaRef, ctx: ContextoEstimacion
) -> ResultadoReglaDeTres:
    tramo = _Tramo(
        dias_par=dias_activos(partida.fecha, llegada.fecha, ctx.recesos),
        dias_proyectados=dias_activos(llegada.fecha, ctx.entrada.fecha_objetivo, ctx.recesos),
    )
    tasa_diaria = (llegada.valor - partida.valor) / tramo.dias_par
    estimado = _proyectar(llegada, tasa_diaria, tramo)
    return ResultadoReglaDeTres(
        estimado=estimado,
        impresiones=estimado - ctx.entrada.ultimo_contador_facturado.valor,
        dias_par=tramo.dias_par,
        dias_proyectados=tramo.dias_proyectados,
        dias_receso_descontados=_receso_total(partida, llegada, ctx),
        tasa_diaria=tasa_diaria,
    )


def _proyectar(llegada: LecturaRef, tasa_diaria: float, tramo: _Tramo) -> float:
    return llegada.valor + tasa_diaria * tramo.dias_proyectados


def _receso_total(partida: LecturaRef, llegada: LecturaRef, ctx: ContextoEstimacion) -> int:
    receso_par = dias_receso_en_tramo(partida.fecha, llegada.fecha, ctx.recesos)
    receso_proyeccion = dias_receso_en_tramo(llegada.fecha, ctx.entrada.fecha_objetivo, ctx.recesos)
    return receso_par + receso_proyeccion

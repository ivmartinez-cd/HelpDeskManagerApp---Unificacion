from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from src.modules.contadores.domain.services.estimacion.aritmetica_decimal_cs import (
    dividir,
    multiplicar,
    sumar,
)
from src.modules.contadores.domain.services.estimacion.recesos import (
    dias_activos_par,
    dias_activos_proyeccion,
)
from src.modules.contadores.domain.services.estimacion.redondeo import (
    a_decimal,
    a_float,
    contador_anterior_o_cero,
    redondear,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef


@dataclass(frozen=True, slots=True)
class _Tramo:
    dias_par: int
    dias_par_calendario: int
    dias_proyectados: int
    dias_receso: int


@dataclass(frozen=True, slots=True)
class ReglaDeTres:
    """Regla de tres Partida→Llegada→fecha objetivo, sin redondear — el
    cálculo común de `EstimarEntreReales` y `RecalcularConPL` del legacy.
    `dias_proyectados` es negativo si la Llegada es posterior a la fecha
    objetivo (interpolación hacia atrás). `dias_receso` es el "receso −Nd"
    del detalle: días de receso del par más los de la proyección."""

    llegada_proyectada: Decimal
    impresiones: Decimal
    tasa_diaria: Decimal
    dias_par: int
    dias_par_calendario: int
    dias_proyectados: int
    dias_receso: int

    @property
    def ajustado_por_receso(self) -> bool:
        return self.dias_receso > 0


def calcular_regla_de_tres(
    partida: LecturaRef, llegada: LecturaRef, ctx: ContextoEstimacion
) -> ReglaDeTres:
    tramo = _tramo(partida.fecha, llegada.fecha, ctx)
    tasa = dividir(a_decimal(llegada.valor) - a_decimal(partida.valor), tramo.dias_par)
    proyectada = sumar(a_decimal(llegada.valor), multiplicar(tasa, tramo.dias_proyectados))
    return ReglaDeTres(
        llegada_proyectada=proyectada,
        impresiones=sumar(proyectada, -contador_anterior_o_cero(ctx.entrada)),
        tasa_diaria=tasa,
        dias_par=tramo.dias_par,
        dias_par_calendario=tramo.dias_par_calendario,
        dias_proyectados=tramo.dias_proyectados,
        dias_receso=tramo.dias_receso,
    )


def _tramo(partida: date, llegada: date, ctx: ContextoEstimacion) -> _Tramo:
    objetivo = ctx.entrada.fecha_objetivo
    dias_calendario = (llegada - partida).days
    dias_par = dias_activos_par(partida, llegada, ctx.recesos)
    dias_proyectados = dias_activos_proyeccion(llegada, objetivo, ctx.recesos)
    receso_proyeccion = abs((objetivo - llegada).days) - abs(dias_proyectados)
    receso_par = dias_calendario - dias_par
    return _Tramo(dias_par, dias_calendario, dias_proyectados, receso_par + receso_proyeccion)


def campos_regla_de_tres(r3: ReglaDeTres) -> dict[str, Any]:
    """Campos del resultado comunes a entre reales y P/L manual: valores
    redondeados como el legacy (`Math.Round(x, 0)`; `PromedioDiario` a 2
    decimales) más la trazabilidad del tramo."""
    return dict(
        estim_propuesto=a_float(redondear(r3.llegada_proyectada)),
        impresiones=a_float(redondear(r3.impresiones)),
        dias_par_pl=r3.dias_par,
        dias_proyectados=r3.dias_proyectados,
        tasa_diaria=a_float(redondear(r3.tasa_diaria, 2)),
        ajustado_por_receso=r3.ajustado_por_receso,
        dias_receso_descontados=r3.dias_receso,
    )

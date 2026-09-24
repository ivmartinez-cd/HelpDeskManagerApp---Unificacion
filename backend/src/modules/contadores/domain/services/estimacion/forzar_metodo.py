"""`ForzarCascada` y `ForzarEntreReales` del legacy: el operador ignora lo que
decidió la cascada automática y fuerza un método puntual, aunque hubiera uno
"mejor" disponible (historia propia, T4)."""

from dataclasses import replace

from src.modules.contadores.domain.services.estimacion.entre_dos_reales import (
    estimar_entre_reales,
    hay_par_entre_reales,
)
from src.modules.contadores.domain.services.estimacion.marcadores import finalizar
from src.modules.contadores.domain.services.estimacion.parque import estimar_cascada_t19
from src.modules.contadores.domain.services.estimacion.resultados_sin_estimacion import (
    resultado_pendiente,
)
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)

_PREFIJO_CASCADA = "Forzado a T19 (cascada) por operador · "
_PREFIJO_ENTRE_REALES = "Forzado a entre reales por operador · "


def forzar_entre_reales(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """Regla de tres sobre el par real anterior / último real — `None` solo
    si no hay par válido (15 días y último real mayor). No importa si la
    historia está vieja, ni si había un T4 mejor, y un negativo se conserva:
    el operador decidió confiar en este par."""
    if not hay_par_entre_reales(ctx.entrada):
        return None
    return _forzado(estimar_entre_reales(ctx), ctx, _PREFIJO_ENTRE_REALES)


def forzar_cascada_parque(ctx: ContextoEstimacion) -> EstimacionResultado:
    """Cascada de parque T19 aunque hubiera un método mejor. Si ningún nivel
    tiene datos, el resultado forzado es la fila pendiente (como el legacy:
    `EstimarCascadaT19 ?? Pendiente`), nunca `None`."""
    borrador = estimar_cascada_t19(ctx) or resultado_pendiente()
    return _forzado(borrador, ctx, _PREFIJO_CASCADA)


def _forzado(
    borrador: EstimacionResultado, ctx: ContextoEstimacion, prefijo: str
) -> EstimacionResultado:
    """Prefijo en el detalle y marca `ForzadoPorOperador` — salvo en la fila
    pendiente, que en el legacy no tiene decisión donde anotar la marca."""
    final = finalizar(borrador, ctx.entrada)
    marcas = final.marcas
    if final.fuente != "Pendiente":
        marcas = marcas | {"ForzadoPorOperador"}
    return replace(final, detalle_calculo=prefijo + final.detalle_calculo, marcas=marcas)

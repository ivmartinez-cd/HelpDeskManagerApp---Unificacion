"""Dos de las cinco acciones manuales del operador (REGLAS_DE_NEGOCIO §8):
ignoran lo que decidió la cascada automática y fuerzan un método puntual,
aunque hubiera uno "mejor" disponible (historia propia, T4). Las otras tres
acciones (elegir P/L a mano, marcar pendiente, agregar nota) ya existían
antes de este archivo — ver `recalcular_manual.py` y
`decisiones_operador_store.py`."""

from src.modules.contadores.domain.services.estimacion.antiguedad import historia_en_alerta
from src.modules.contadores.domain.services.estimacion.entre_dos_reales import (
    intentar_entre_dos_reales,
)
from src.modules.contadores.domain.services.estimacion.parque import intentar_parque
from src.modules.contadores.domain.services.estimacion.validez_t4 import par_valido
from src.modules.contadores.domain.value_objects.estimacion.contexto_estimacion import (
    ContextoEstimacion,
)
from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)


def forzar_entre_reales(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """Fuerza la regla de tres sobre el par real anterior/último real si
    existe y es válido — `None` si no hay par o el par no cumple las reglas
    de validez de §5.2 (15 días, Llegada ≥ Partida). A diferencia del cálculo
    automático, no importa si la historia está "vieja" (en alerta) ni si
    había un T4 mejor: el operador decidió confiar en este par igual."""
    entrada = ctx.entrada
    if entrada.ultimo_real is None or entrada.real_anterior is None:
        return None
    if not par_valido(entrada.real_anterior, entrada.ultimo_real):
        return None
    return intentar_entre_dos_reales(ctx)


def forzar_cascada_parque(ctx: ContextoEstimacion) -> EstimacionResultado | None:
    """Fuerza la cascada de parque (§5.5) aunque hubiera un método mejor
    disponible — `None` si ningún nivel de parque tiene datos suficientes
    (mismo criterio que el cálculo automático, el operador no puede forzar
    un dato que no existe)."""
    entrada = ctx.entrada
    en_alerta = historia_en_alerta(entrada.ultimo_real, entrada.tecnologia, entrada.fecha_objetivo)
    return intentar_parque(ctx, en_alerta)

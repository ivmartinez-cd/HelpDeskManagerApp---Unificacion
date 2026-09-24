from src.modules.contadores.domain.value_objects.estimacion.estimacion_resultado import (
    EstimacionResultado,
)
from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import (
    FuenteEstimacion,
    Semaforo,
)

# Parque_Cliente_Tec NO está: en el legacy queda AMARILLO (pide confirmación
# como toda la cascada, pero no es rojo). "Pendiente" es `RequierePendiente`.
_FUENTES_ROJAS: frozenset[FuenteEstimacion] = frozenset(
    {"Parque_Cliente_Modelo", "Parque_Grupo_Modelo", "Parque_Global_Modelo", "Pendiente"}
)


def resolver_semaforo(resultado: EstimacionResultado, t4_revisado: bool) -> Semaforo:
    """`CalcularSemaforo` del legacy para una fila pendiente de estimar (la
    fila ya real es siempre VERDE y no pasa por acá). Evalúa en orden: el
    primero que aplica define el color. Espera `borde_salto_imposible` y
    `coloreo` ya calculados."""
    if resultado.borde_salto_imposible or resultado.fuente in _FUENTES_ROJAS:
        return "ROJO"
    if resultado.fuente == "T4_ST" and not t4_revisado:
        return "AMARILLO"
    if resultado.requiere_confirmacion:
        return "AMARILLO"
    if resultado.coloreo in ("AZUL", "NARANJA"):
        return "NARANJA"
    return "VERDE"

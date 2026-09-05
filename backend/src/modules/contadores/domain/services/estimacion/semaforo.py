from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import Semaforo


@dataclass(frozen=True, slots=True)
class SenalesSemaforo:
    """Condiciones ya evaluadas por el motor, en el orden exacto que
    REGLAS_DE_NEGOCIO §7.3 define para decidir el color final."""

    ya_real: bool
    salto_imposible: bool
    es_cascada_parque: bool
    pendiente: bool
    t4_sin_revisar: bool
    requiere_confirmacion_otro_motivo: bool
    coloreo_activo: bool


def resolver_semaforo(senales: SenalesSemaforo) -> Semaforo:
    """Evalúa en orden — el primero que aplica define el color final."""
    if senales.ya_real:
        return "VERDE"
    if senales.salto_imposible:
        return "ROJO"
    if senales.es_cascada_parque:
        return "ROJO"
    if senales.pendiente:
        return "ROJO"
    if senales.t4_sin_revisar:
        return "AMARILLO"
    if senales.requiere_confirmacion_otro_motivo:
        return "AMARILLO"
    if senales.coloreo_activo:
        return "NARANJA"
    return "VERDE"

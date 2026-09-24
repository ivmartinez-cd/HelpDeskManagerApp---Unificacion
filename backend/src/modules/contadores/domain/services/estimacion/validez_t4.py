from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

ANTIGUEDAD_MAXIMA_T4_SIN_REAL_DIAS = 60  # MaxDiasT4SinReal del legacy
DIAS_MINIMOS_SEPARACION_PL = 15  # MinDiasSeparacion del legacy


def t4_llegada_valida(
    fecha_t4: date | None, fecha_ultimo_real_no_t4: date | None, fecha_objetivo: date
) -> bool:
    """`T4LlegadaValida` del legacy: con un real no-T4, el T4 sirve solo si
    es posterior a esa lectura; sin ninguno, mientras no tenga más de 60 días
    respecto de la fecha objetivo."""
    if fecha_t4 is None:
        return False
    if fecha_ultimo_real_no_t4 is not None:
        return fecha_t4 > fecha_ultimo_real_no_t4
    return (fecha_objetivo - fecha_t4).days <= ANTIGUEDAD_MAXIMA_T4_SIN_REAL_DIAS


def par_entre_reales_valido(real_anterior: LecturaRef, ultimo_real: LecturaRef) -> bool:
    """`PuedeCalcularEntreReales` del legacy: al menos 15 días entre ambas y
    el último real ESTRICTAMENTE mayor — un contador sin movimiento no sirve
    de par y la fila cae a T4 / parque."""
    dias = (ultimo_real.fecha - real_anterior.fecha).days
    return dias >= DIAS_MINIMOS_SEPARACION_PL and ultimo_real.valor > real_anterior.valor


def par_valido(partida: LecturaRef, llegada: LecturaRef) -> bool:
    """Validez de una pareja P/L elegida a mano (`RecalcularConPL`): al
    menos 15 días y Llegada no menor que Partida (acá sí se acepta Δ=0)."""
    dias = (llegada.fecha - partida.fecha).days
    return dias >= DIAS_MINIMOS_SEPARACION_PL and llegada.valor >= partida.valor

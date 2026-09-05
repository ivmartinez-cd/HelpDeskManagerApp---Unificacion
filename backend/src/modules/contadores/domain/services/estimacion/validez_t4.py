from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

ANTIGUEDAD_MAXIMA_T4_SIN_REAL_DIAS = 60
DIAS_MINIMOS_SEPARACION_PL = 15


def t4_es_valido(
    t4: LecturaRef | None, fecha_ultimo_real_no_t4: date | None, fecha_objetivo: date
) -> bool:
    """Protege contra usar un T4 ya superado (REGLAS_DE_NEGOCIO §5.3). Con
    un real no-T4 facturado, el T4 sirve solo si es posterior a esa lectura.
    Sin ningún real no-T4, el T4 se usa igual mientras sea reciente."""
    if t4 is None:
        return False
    if fecha_ultimo_real_no_t4 is not None:
        return t4.fecha > fecha_ultimo_real_no_t4
    return (fecha_objetivo - t4.fecha).days <= ANTIGUEDAD_MAXIMA_T4_SIN_REAL_DIAS


def par_valido(partida: LecturaRef, llegada: LecturaRef) -> bool:
    """Reglas de validez del par, aplican tanto al cálculo automático como
    al manual (CASOS_DE_PRUEBA §12): separación mínima 15 días calendario,
    Llegada no decreciente respecto de Partida."""
    return (
        llegada.fecha - partida.fecha
    ).days >= DIAS_MINIMOS_SEPARACION_PL and llegada.valor >= partida.valor

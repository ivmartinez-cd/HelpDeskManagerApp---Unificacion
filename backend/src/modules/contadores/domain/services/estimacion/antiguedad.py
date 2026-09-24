from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

UMBRAL_MESES_SIN_REAL: dict[Tecnologia, int] = {"MONO": 12, "COLOR": 6}


def meses_entre(desde: date, hasta: date) -> int:
    """`MesesSinReal` del legacy: meses completos entre dos fechas (un mes
    cuenta solo si `hasta` ya alcanzó el día de `desde`), nunca negativo —
    una lectura posterior a `hasta` da 0."""
    meses = (hasta.year - desde.year) * 12 + (hasta.month - desde.month)
    if hasta.day < desde.day:
        meses -= 1
    return max(0, meses)


def historia_en_alerta(
    ultimo_real: LecturaRef | None, tecnologia: Tecnologia, fecha_objetivo: date
) -> bool:
    """`MesesEnAlerta` del legacy: historia propia demasiado vieja para una
    regla de tres. El umbral es "más de" N meses: exactamente en el límite
    todavía no dispara la alerta."""
    if ultimo_real is None:
        return False
    return meses_entre(ultimo_real.fecha, fecha_objetivo) > UMBRAL_MESES_SIN_REAL[tecnologia]

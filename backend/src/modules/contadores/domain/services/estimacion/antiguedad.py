from datetime import date

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia
from src.modules.contadores.domain.value_objects.estimacion.lectura_ref import LecturaRef

UMBRAL_MESES_SIN_REAL: dict[Tecnologia, int] = {"MONO": 12, "COLOR": 6}


def meses_entre(desde: date, hasta: date) -> int:
    """Meses completos entre dos fechas — un mes solo cuenta si `hasta` ya
    alcanzó el día de `desde` en ese mes (30-abr a 30-abr da 12 exactos, no
    se redondea para arriba)."""
    meses = (hasta.year - desde.year) * 12 + (hasta.month - desde.month)
    if hasta.day < desde.day:
        meses -= 1
    return meses


def historia_en_alerta(
    ultimo_real: LecturaRef | None, tecnologia: Tecnologia, fecha_objetivo: date
) -> bool:
    """Historia propia demasiado vieja para servir de base de una regla de
    tres (REGLAS_DE_NEGOCIO §5.4). El umbral es "más de" N meses, no "N o
    más": exactamente en el límite todavía no dispara la alerta."""
    if ultimo_real is None:
        return False
    return meses_entre(ultimo_real.fecha, fecha_objetivo) > UMBRAL_MESES_SIN_REAL[tecnologia]

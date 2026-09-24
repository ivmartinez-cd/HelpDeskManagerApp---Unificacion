"""Cuentas de días hábiles del semáforo de Despachados (lunes a viernes, sin feriados).

OCA devuelve al remitente lo que no se retira en sucursal dentro de 5 días hábiles, y un
envío que no cambia de estado en N días hábiles merece revisión: las dos cuentas saltean
sábados, domingos y los feriados que recibe quien llama (acá no se calculan feriados).
"""

from datetime import date, timedelta

_UN_DIA = timedelta(days=1)
_SABADO = 5


def es_dia_habil(dia: date, feriados: frozenset[date]) -> bool:
    """Lunes a viernes que no es feriado."""
    return dia.weekday() < _SABADO and dia not in feriados


def siguiente_dia_habil(dia: date, feriados: frozenset[date]) -> date:
    """`dia` si es hábil; si no, el próximo día hábil."""
    while not es_dia_habil(dia, feriados):
        dia += _UN_DIA
    return dia


def fecha_limite_retiro(fecha_ingreso: date, feriados: frozenset[date], dias_habiles: int) -> date:
    """Último día para retirar en sucursal: el `dias_habiles`-ésimo día hábil, contando
    como día 1 el de ingreso (o el primer hábil posterior si ingresó en un día no hábil).
    Ej.: ingreso el lunes 21/09/2026, 5 días -> límite el viernes 25/09/2026."""
    if dias_habiles < 1:
        raise ValueError(f"El plazo tiene que ser de al menos 1 día hábil (llegó {dias_habiles})")
    dia = siguiente_dia_habil(fecha_ingreso, feriados)
    for _ in range(dias_habiles - 1):
        dia = siguiente_dia_habil(dia + _UN_DIA, feriados)
    return dia


def dias_habiles_transcurridos(desde: date, hasta: date, feriados: frozenset[date]) -> int:
    """Días hábiles `d` con `desde < d <= hasta`; 0 si `hasta <= desde`."""
    dias = (desde + _UN_DIA * n for n in range(1, (hasta - desde).days + 1))
    return sum(1 for dia in dias if es_dia_habil(dia, feriados))


def dias_habiles_hasta(hoy: date, limite: date, feriados: frozenset[date]) -> int:
    """Días hábiles que faltan de `hoy` a `limite`: 0 = vence hoy, 1 = vence el próximo día
    hábil, negativo = vencido (-1 si venció el último día hábil). Un límite pasado siempre
    da negativo, aunque hoy no sea hábil: el sábado, un límite del viernes da -1, no 0."""
    if limite >= hoy:
        return dias_habiles_transcurridos(hoy, limite, feriados)
    return -max(1, dias_habiles_transcurridos(limite, hoy, feriados))

"""Conteo de días de una solicitud (calendarDaysBetween del legacy).

Días CORRIDOS inclusive, con extensión LCT: si el fin cae viernes se extiende
+2 (sábado y domingo), si cae sábado +1 (domingo). Los feriados dentro o al
final del rango cuentan igual; el único descuento es un feriado con
`deducts_vacation=False` que caiga exactamente en el día de inicio (desplaza
el comienzo: -1 día).
"""

from datetime import date, timedelta

_VIERNES = 4
_SABADO = 5


def dias_corridos(start: date, end: date) -> int:
    if end < start:
        return 0
    last = end
    dow = end.weekday()
    if dow == _VIERNES:
        last = end + timedelta(days=2)
    elif dow == _SABADO:
        last = end + timedelta(days=1)
    return (last - start).days + 1


def dias_solicitados(start: date, end: date, *, feriado_no_deduce_en_inicio: bool) -> int:
    descuento = 1 if feriado_no_deduce_en_inicio else 0
    return max(0, dias_corridos(start, end) - descuento)

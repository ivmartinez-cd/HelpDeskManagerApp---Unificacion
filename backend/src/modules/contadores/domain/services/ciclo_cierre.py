"""Ciclo de cierre mensual de facturación de contadores: rota el día
DIA_CIERRE de cada mes. Espejo de `getCicloCierre` en
frontend/src/features/home/components/facturacion-parts.tsx — misma regla
en los dos lenguajes; si el día de corte cambia, actualizar ambos.

El período se nombra por el mes en que ARRANCA (convención Siges, ver
`periodos_facturacion.periodo_de`): el período "202607" va del 20/7 al 20/8,
el "202608" del 20/8 al 20/9 — el día DIA_CIERRE es a la vez cierre del
período que termina y arranque del que empieza."""

from datetime import date

DIA_CIERRE = 20


def ventana_periodo_actual(hoy: date) -> tuple[date, date]:
    """[inicio, próximo cierre] del período de facturación en curso. Del 1 al
    DIA_CIERRE todavía se factura el período que cierra este mes (arrancó el
    DIA_CIERRE del mes anterior); desde el día siguiente ya arrancó, EL
    DIA_CIERRE de este mes, el período que cierra el mes que viene."""
    cierre_este_mes = date(hoy.year, hoy.month, DIA_CIERRE)
    if hoy <= cierre_este_mes:
        inicio = _sumar_meses(cierre_este_mes, -1)
        fin = cierre_este_mes
    else:
        inicio = cierre_este_mes
        fin = _sumar_meses(cierre_este_mes, 1)
    return inicio, fin


def _sumar_meses(dia: date, n: int) -> date:
    total = dia.year * 12 + (dia.month - 1) + n
    return date(total // 12, total % 12 + 1, dia.day)

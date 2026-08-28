"""Aritmética de períodos de facturación (formato Siges YYYYMM) y regla de
estado del reporte de cierre de contadores.

Regla pedida por la TL (2026-08-14): el período inmediato anterior pendiente
es EN PROCESO (cierre en curso normal) y todo período más viejo es DEMORADO.
Es la misma semántica del legacy `AnexosNoFacturados` con la referencia
puesta en el mes anterior (en el legacy el label depende del período de
referencia elegido a mano; acá la referencia rueda sola con el calendario).
El mes en curso, antes afuera del todo, se anota como MES_EN_CURSO desde
2026-08-28 — filtro aparte para quien necesite ver el arrastre que todavía
no cerró, sin mezclarlo con los KPIs de pendientes/demorados del cierre."""

from datetime import date
from typing import Literal

EstadoAnexoPendiente = Literal["en_proceso", "demorado", "mes_en_curso"]


def periodo_de(dia: date) -> str:
    return f"{dia.year:04d}{dia.month:02d}"


def periodo_anterior(periodo: str) -> str:
    anio, mes = int(periodo[:4]), int(periodo[4:])
    if mes == 1:
        return f"{anio - 1:04d}12"
    return f"{anio:04d}{mes - 1:02d}"


def restar_meses(dia: date, meses: int) -> date:
    """Primer día del mes que queda `meses` atrás — el corte de la ventana
    de recencia sobre `Fecha_Proceso` (ver `anexos_pendientes_query.py`)."""
    indice = dia.year * 12 + (dia.month - 1) - meses
    return date(indice // 12, indice % 12 + 1, 1)


def estado_de_periodo(periodo: str, *, hoy: date) -> EstadoAnexoPendiente:
    if periodo == periodo_de(hoy):
        return "mes_en_curso"
    if periodo >= periodo_anterior(periodo_de(hoy)):
        return "en_proceso"
    return "demorado"

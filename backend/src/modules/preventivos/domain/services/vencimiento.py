"""Cálculo puro del vencimiento del preventivo de un equipo — sin DB, sin
reloj propio (recibe `hoy`), testeable en aislamiento."""

from datetime import date, timedelta

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    EstadoPreventivo,
    VencimientoPreventivo,
)

# Un preventivo que vence dentro de este margen ya es accionable para el
# operador (planificar la visita), aunque todavía no esté vencido.
UMBRAL_POR_VENCER_DIAS = 30

# Menor número = más urgente. Ordena la tabla (vencidos primero, más atrasado
# arriba) y decide el "peor estado" de una sucursal con varias máquinas en el
# mapa — misma semántica, un solo lugar.
ORDEN_ESTADO_PRIORIDAD: dict[EstadoPreventivo, int] = {
    "vencido": 0,
    "sin_preventivo": 1,
    "por_vencer": 2,
    "al_dia": 3,
    "sin_frecuencia": 4,
}


def calcular_vencimiento(
    fecha_ultimo_preventivo: date | None,
    frecuencia_dias: int | None,
    hoy: date,
    umbral_por_vencer_dias: int = UMBRAL_POR_VENCER_DIAS,
    fecha_instalacion: date | None = None,
) -> VencimientoPreventivo:
    if frecuencia_dias is None or frecuencia_dias <= 0:
        return VencimientoPreventivo("sin_frecuencia", None, None)
    if fecha_ultimo_preventivo is None:
        tentativa = _fecha_tentativa(fecha_instalacion, frecuencia_dias)
        return VencimientoPreventivo("sin_preventivo", None, None, fecha_tentativa=tentativa)
    proximo = fecha_ultimo_preventivo + timedelta(days=frecuencia_dias)
    if proximo < hoy:
        return VencimientoPreventivo("vencido", proximo, (hoy - proximo).days)
    if proximo <= hoy + timedelta(days=umbral_por_vencer_dias):
        return VencimientoPreventivo("por_vencer", proximo, None)
    return VencimientoPreventivo("al_dia", proximo, None)


def _fecha_tentativa(fecha_instalacion: date | None, frecuencia_dias: int) -> date | None:
    if fecha_instalacion is None:
        return None
    return fecha_instalacion + timedelta(days=frecuencia_dias)

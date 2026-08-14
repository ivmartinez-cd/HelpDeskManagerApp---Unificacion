"""Cálculo puro del vencimiento del preventivo de un equipo — sin DB, sin
reloj propio (recibe `hoy`), testeable en aislamiento."""

from datetime import date, timedelta

from src.modules.preventivos.domain.value_objects.vencimiento_preventivo import (
    VencimientoPreventivo,
)

# Un preventivo que vence dentro de este margen ya es accionable para el
# operador (planificar la visita), aunque todavía no esté vencido.
UMBRAL_POR_VENCER_DIAS = 30


def calcular_vencimiento(
    fecha_ultimo_preventivo: date | None,
    frecuencia_dias: int | None,
    hoy: date,
    umbral_por_vencer_dias: int = UMBRAL_POR_VENCER_DIAS,
) -> VencimientoPreventivo:
    if frecuencia_dias is None or frecuencia_dias <= 0:
        return VencimientoPreventivo("sin_frecuencia", None, None)
    if fecha_ultimo_preventivo is None:
        return VencimientoPreventivo("sin_preventivo", None, None)
    proximo = fecha_ultimo_preventivo + timedelta(days=frecuencia_dias)
    if proximo < hoy:
        return VencimientoPreventivo("vencido", proximo, (hoy - proximo).days)
    if proximo <= hoy + timedelta(days=umbral_por_vencer_dias):
        return VencimientoPreventivo("por_vencer", proximo, None)
    return VencimientoPreventivo("al_dia", proximo, None)

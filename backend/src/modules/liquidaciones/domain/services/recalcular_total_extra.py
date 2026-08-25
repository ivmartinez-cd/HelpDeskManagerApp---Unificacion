"""Recalcula `total_importe` cuando cambia el ítem extra de una liquidación.

`total_importe` = suma de `costo_total_cobrado` de los incidentes + `monto_extra`
(desde 2026-08-25 — antes el extra quedaba fuera del total mostrado en listado,
dashboard y detalle: hallazgo real, liquidación 3907-5 de San Juan con extra
cargado que seguía mostrando el total viejo). Los dos call sites que cambian el
extra (reconciliación con AyC, PATCH manual) no tienen a mano la suma de
incidentes, así que ajustan por delta sobre el total vigente en vez de
recalcular desde cero — requiere que `liquidacion.total_importe` ya incluya el
extra viejo, invariante que mantiene `total_importe_con_incidentes_y_extra`."""

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion


def total_importe_con_incidentes_y_extra(
    incidentes_costo_total: float, monto_extra: float | None
) -> float:
    return round(incidentes_costo_total + (monto_extra or 0.0), 2)


def total_importe_tras_cambiar_extra(
    liquidacion: Liquidacion, nuevo_monto_extra: float | None
) -> float:
    delta = (nuevo_monto_extra or 0.0) - (liquidacion.monto_extra or 0.0)
    return round(liquidacion.total_importe + delta, 2)

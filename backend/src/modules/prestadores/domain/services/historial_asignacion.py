"""Reglas del historial de asignación de operador por PST: los tramos de un
PST nunca se solapan y a lo sumo uno está abierto (`hasta=None`)."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

_ONE_DAY = timedelta(days=1)


class TramoLike(Protocol):
    """Lo mínimo que necesita la regla: sirve tanto para la entidad como para
    el modelo de persistencia, así el repositorio real y el fake aplican
    exactamente el mismo recorte."""

    @property
    def desde(self) -> date: ...

    @property
    def hasta(self) -> date | None: ...


@dataclass(frozen=True, slots=True)
class PlanReasignacion[T: TramoLike]:
    borrar: list[T]
    """Tramos que empiezan en `desde` o después: nunca llegan a cubrir un día
    antes del nuevo tramo, así que no tienen valor histórico."""
    cerrar: list[T]
    """Tramos que alcanzan `desde` (abiertos o cerrados después): se recortan
    a `cierre` (= `desde - 1 día`)."""
    cierre: date


def planificar_reasignacion[T: TramoLike](tramos: list[T], desde: date) -> PlanReasignacion[T]:
    """Decide qué hacer con los tramos existentes de un PST antes de abrir
    uno nuevo en `desde`. Considera también los tramos futuros ya cerrados
    (asignaciones programadas y luego pisadas por una anterior), no solo el
    vigente — de lo contrario quedaban solapes."""
    return PlanReasignacion(
        borrar=[t for t in tramos if t.desde >= desde],
        cerrar=[t for t in tramos if t.desde < desde and (t.hasta is None or t.hasta >= desde)],
        cierre=desde - _ONE_DAY,
    )


def operador_vigente[T: TramoLike](tramos: list[T], fecha: date) -> T | None:
    """El tramo que cubre `fecha`, si hay uno (sin solapes hay a lo sumo uno)."""
    for tramo in tramos:
        if tramo.desde <= fecha and (tramo.hasta is None or tramo.hasta >= fecha):
            return tramo
    return None

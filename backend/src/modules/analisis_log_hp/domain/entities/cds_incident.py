"""Incidente CD (Canal Directo, vía wsAyC) asociado a un equipo por serial."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CdsReplacement:
    articulo: str
    cantidad: int


@dataclass(frozen=True)
class CdsIncident:
    id: str
    numero_incidente: str
    fecha: str
    fecha_cierre: str | None
    tipo: str
    estado: str
    motivo: str
    contador: str | None
    repuestos: list[CdsReplacement]
    tareas_realizadas: list[str]

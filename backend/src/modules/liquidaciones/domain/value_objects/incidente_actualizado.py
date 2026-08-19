"""Incidente local cuyos campos difieren de lo que reporta AyC — salida de
`reconciliar_incidentes`, entrada de `IncidenteRepository.update_cobrados`.

Trae el `incidente_id` local (para el UPDATE in-place — nunca se borra y recrea un
incidente que sigue existiendo remotamente, ver `reconciliar_incidentes.py`) y el
valor completo y ya normalizado de cada campo comparable, no un delta parcial."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class IncidenteActualizado:
    incidente_id: UUID
    rubro: str
    tipo: str
    empresa_nombre: str
    sucursal_nombre: str
    nro_serie: str
    fecha_cierre: date | None
    costo_servicio_cobrado: float
    cant_km_cobrado: float
    costo_km_cobrado: float
    total_viaje_cobrado: float
    costo_total_cobrado: float
    pasa_it: bool

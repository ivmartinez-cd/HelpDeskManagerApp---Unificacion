"""Incidente cuyos campos difieren de lo que reporta AyC, con el detalle campo a
campo — a diferencia de `IncidenteActualizado` (que solo lleva el valor final
para el UPDATE in-place), esto conserva el antes/después para registrar un
`ModificacionPrestador` (ver `application/use_cases/_registrar_modificaciones.py`)."""

from dataclasses import dataclass
from uuid import UUID

from src.modules.liquidaciones.domain.value_objects.campo_modificado import CampoModificado


@dataclass(frozen=True)
class IncidenteModificado:
    incidente_id: UUID
    numero_incidente: str
    campos: tuple[CampoModificado, ...]

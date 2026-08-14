from dataclasses import dataclass

from src.modules.contadores.domain.entities.equipo_sin_real import EquipoSinReal


@dataclass(frozen=True, slots=True)
class OperadorAsignado:
    """Operador de facturación que tiene planificado al cliente del equipo
    (según el calendario local sincronizado de Gestión)."""

    nombre: str
    color: str | None


@dataclass(frozen=True, slots=True)
class EquipoSinRealAnotado:
    """Equipo sin real + el operador asignado a su cliente. `operador=None`
    cuando el cliente no cruza con el calendario (o el cruce degradó)."""

    equipo: EquipoSinReal
    operador: OperadorAsignado | None

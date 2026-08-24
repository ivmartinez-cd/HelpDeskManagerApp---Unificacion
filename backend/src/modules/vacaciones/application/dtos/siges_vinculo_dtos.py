import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PropuestaVinculoEmpleado:
    empleado_id: uuid.UUID
    empleado_nombre: str
    siges_empresa_id: int
    siges_den_comercial: str


@dataclass(frozen=True, slots=True)
class SigesTecnicoDisponibleDTO:
    siges_empresa_id: int
    den_comercial: str


@dataclass(frozen=True, slots=True)
class PropuestasVinculoEmpleadoResultado:
    propuestas: list[PropuestaVinculoEmpleado]
    disponibles: list[SigesTecnicoDisponibleDTO]

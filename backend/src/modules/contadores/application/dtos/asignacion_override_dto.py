import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class AsignacionOverrideDTO:
    id: uuid.UUID
    operador_ausente_id: str
    operador_ausente_nombre: str | None
    operador_reemplazante_id: str
    operador_reemplazante_nombre: str | None
    vigente_desde: date
    vigente_hasta: date
    alcance_total: bool
    clientes: list[str]
    estado: str
    motivo: str | None

import uuid
from dataclasses import dataclass, field
from datetime import datetime

# Vocabulario del legacy VacaSync (AuditLog.action / AuditLog.entity). Se
# conservan los mismos strings para que la migración de datos reales quede
# uniforme con lo que escribe el módulo nuevo.
ACCION_CREATE = "CREATE"
ACCION_UPDATE = "UPDATE"
ACCION_DELETE = "DELETE"
ACCION_APPROVE = "APPROVE"
ACCION_REJECT = "REJECT"
ACCION_IMPORT = "IMPORT"

ENTIDAD_SECTOR = "Department"
ENTIDAD_EMPLEADO = "Employee"
ENTIDAD_CARGO = "Position"
ENTIDAD_FERIADO = "Holiday"
ENTIDAD_SOLICITUD = "VacationRequest"
ENTIDAD_CONFIG = "SystemConfig"
ENTIDAD_AUSENCIA = "Absence"


@dataclass(slots=True, eq=False)
class RegistroAuditoria:
    """Entrada del log de auditoría del módulo (AuditLog legacy)."""

    id: uuid.UUID
    accion: str
    entidad: str
    entidad_id: str | None
    user_id: uuid.UUID | None
    created_at: datetime
    metadata: dict[str, object] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RegistroAuditoria) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

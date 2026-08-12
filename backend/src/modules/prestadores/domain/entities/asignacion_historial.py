import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, eq=False)
class AsignacionHistorial:
    """Un tramo de "quién atendió este PST": `operador_id=None` representa un
    tramo sin operador asignado (ej. tras la baja de quien lo llevaba, antes de
    reasignarlo). `hasta=None` = tramo vigente."""

    id: uuid.UUID
    prestador_id: uuid.UUID
    operador_id: uuid.UUID | None
    desde: date
    hasta: date | None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AsignacionHistorial) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

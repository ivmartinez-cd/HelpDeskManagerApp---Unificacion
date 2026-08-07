import uuid
from dataclasses import dataclass
from datetime import datetime

from src.modules.contadores.domain.value_objects.meter_source import MeterSource


@dataclass(slots=True, eq=False)
class MeterClientConfig:
    """Preferencia guardada por cliente SDS/ERS: si sus contadores mono+color
    se combinan en uno solo (`suma_color`) al exportar. Clave lógica es
    (source, customer_id) — ver UniqueConstraint del modelo."""

    id: uuid.UUID
    source: MeterSource
    customer_id: str
    customer_name: str
    suma_color: bool
    updated_at: datetime

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MeterClientConfig) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

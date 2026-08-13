import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class CreateAsignacionOverrideRequest:
    operador_ausente_id: str
    operador_reemplazante_id: str
    vigente_desde: date
    vigente_hasta: date
    clientes: list[str] | None
    """`None` = alcance TOTAL; lista (vacía o con nombres) = alcance por
    cliente puntual."""
    motivo: str | None
    created_by_user_id: uuid.UUID

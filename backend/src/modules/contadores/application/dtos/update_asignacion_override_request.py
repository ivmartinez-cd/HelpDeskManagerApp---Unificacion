import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class UpdateAsignacionOverrideRequest:
    """Edición in-place de un override ACTIVA (ver ADR-013, actualización
    2026-08-14). Sin `created_by_user_id`: se conserva el del alta."""

    override_id: uuid.UUID
    operador_ausente_id: str
    operador_reemplazante_id: str
    vigente_desde: date
    vigente_hasta: date
    clientes: list[str] | None
    """`None` = alcance TOTAL; lista (vacía o con nombres) = alcance por
    cliente puntual."""
    motivo: str | None

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(slots=True, eq=False)
class AsignacionOverride:
    """Sustitución temporal de operador para uno o más PST (vacaciones,
    licencia). No toca `Prestador.operador_id` ni `AsignacionHistorial` — se
    resuelve en lectura sobre la asignación permanente, nunca la reemplaza en
    la base (ver ADR-013). `hasta` es siempre obligatorio: a diferencia de
    `AsignacionHistorial.hasta`, acá no existe vigencia abierta, por diseño."""

    id: uuid.UUID
    operador_ausente_id: uuid.UUID
    operador_reemplazante_id: uuid.UUID
    desde: date
    hasta: date
    alcance: Literal["TOTAL"] | frozenset[uuid.UUID]
    estado: Literal["ACTIVA", "CANCELADA"]
    motivo: str | None
    created_by_user_id: uuid.UUID

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AsignacionOverride) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

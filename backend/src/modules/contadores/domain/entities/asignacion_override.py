import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(slots=True, eq=False)
class AsignacionOverride:
    """Sustitución temporal de operador para uno o más clientes (vacaciones,
    licencia). No toca los eventos sincronizados ni `contadores_operadores`
    — se resuelve en lectura sobre la asignación real de cada evento, nunca
    la reemplaza en la base (ver ADR-013). `operador_ausente_id`/
    `operador_reemplazante_id` son usernames de Gestión (mismo id que
    `Operador.id`), sin FK a `contadores_operadores`: esa tabla se poda en
    cada sync y una FK dura se rompería. `vigente_hasta` es siempre
    obligatorio — a diferencia de `AsignacionHistorial` (prestadores), acá no
    existe vigencia abierta, por diseño."""

    id: uuid.UUID
    operador_ausente_id: str
    operador_reemplazante_id: str
    vigente_desde: date
    vigente_hasta: date
    alcance: Literal["TOTAL"] | frozenset[str]
    """`frozenset[str]` = nombres de cliente exactos (texto libre, sin
    catálogo con ID propio — mismo tipo de aproximación que `Operador.color`
    tenía antes de ADR-012)."""
    estado: Literal["ACTIVA", "CANCELADA"]
    motivo: str | None
    created_by_user_id: uuid.UUID

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AsignacionOverride) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

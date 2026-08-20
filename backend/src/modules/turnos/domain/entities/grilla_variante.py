import uuid
from dataclasses import dataclass, field
from datetime import date, time
from typing import Literal

EstadoVariante = Literal["ACTIVA", "CANCELADA"]


@dataclass(slots=True, eq=False)
class VarianteSlot:
    """Franja de una grilla variante. Tiene id propio (no referencia
    `turno_slot`): la variante es una grilla completa, no un diff sobre la
    titular (ver ADR-025)."""

    id: uuid.UUID
    casilla_id: uuid.UUID
    dia_semana: int  # 0=lunes … 6=domingo
    hora_inicio: time
    hora_fin: time
    sort_order: int
    user_ids: list[uuid.UUID] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, VarianteSlot) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(slots=True, eq=False)
class GrillaVariante:
    """Grilla alternativa de turnos vigente en un rango de fechas (modo
    vacaciones, ADR-025). Se resuelve en lectura en lugar de la grilla
    titular; al pasar `hasta` deja de aplicar sola, sin job. `hasta` es
    obligatorio: temporal por diseño, igual que las coberturas ADR-013."""

    id: uuid.UUID
    motivo: str | None
    origen_texto: str | None
    desde: date
    hasta: date
    estado: EstadoVariante
    created_by_user_id: uuid.UUID
    slots: list[VarianteSlot] = field(default_factory=list)

    def vigente_en(self, fecha: date) -> bool:
        return self.estado == "ACTIVA" and self.desde <= fecha <= self.hasta

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GrillaVariante) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

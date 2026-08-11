import uuid
from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True, slots=True)
class CasillaDTO:
    id: uuid.UUID
    nombre: str
    color: str | None
    sort_order: int
    is_active: bool


@dataclass(frozen=True, slots=True)
class AsignacionDTO:
    id: uuid.UUID
    slot_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None
    vigente_desde: date
    vigente_hasta: date | None


@dataclass(frozen=True, slots=True)
class SlotDTO:
    id: uuid.UUID
    casilla_id: uuid.UUID
    hora_inicio: time
    hora_fin: time
    dia_semana: int
    sort_order: int
    asignaciones: list[AsignacionDTO]


@dataclass(frozen=True, slots=True)
class OperatorShiftView:
    user_id: uuid.UUID
    user_name: str
    color: str | None


@dataclass(frozen=True, slots=True)
class ResolvedShiftDTO:
    slot_id: uuid.UUID
    casilla_id: uuid.UUID
    casilla_nombre: str
    casilla_color: str | None
    hora_inicio: time
    hora_fin: time
    dia_semana: int
    operadores: list[OperatorShiftView]
    is_current: bool
    is_next: bool


@dataclass(frozen=True, slots=True)
class CreateCasillaCommand:
    nombre: str
    color: str | None
    sort_order: int = 0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateCasillaCommand:
    """Solo `nombre` es editable por este comando -- es el único campo que la UI
    expone hoy. `color`/`sort_order`/`is_active` los preserva `UpsertCasilla.update()`
    desde el registro existente; si en el futuro se necesita editarlos, agregarlos acá
    explícitamente en vez de reusar los defaults de `CasillaRequest` (eso fue lo que
    causó que cualquier edición de nombre reseteara color/orden/activo en silencio)."""

    casilla_id: uuid.UUID
    nombre: str


@dataclass(frozen=True, slots=True)
class CreateSlotCommand:
    casilla_id: uuid.UUID
    hora_inicio: time
    hora_fin: time
    dia_semana: int
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class UpdateSlotCommand:
    """Sin `sort_order` a propósito -- la UI no lo edita, `UpsertSlot.update()` lo
    preserva del registro existente (mismo motivo que `UpdateCasillaCommand`)."""

    slot_id: uuid.UUID
    hora_inicio: time
    hora_fin: time
    dia_semana: int


@dataclass(frozen=True, slots=True)
class ReplaceAssignmentsCommand:
    slot_id: uuid.UUID
    user_ids: list[uuid.UUID]
    vigente_desde: date

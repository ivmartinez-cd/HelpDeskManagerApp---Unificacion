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
    # Novedad aprobada del día que afecta al operador ('Home office',
    # 'Horario 08:00–17:00', 'Vacaciones'…); None = jornada normal.
    nota: str | None = None


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


@dataclass(frozen=True, slots=True)
class CreateAsignacionOverrideCommand:
    operador_ausente_id: uuid.UUID
    operador_reemplazante_id: uuid.UUID
    desde: date
    hasta: date
    slot_ids: list[uuid.UUID] | None
    """`None` = alcance TOTAL; lista vacía o con ids = alcance por franja puntual."""
    motivo: str | None
    created_by_user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class UpdateAsignacionOverrideCommand:
    """Edición in-place de una cobertura ACTIVA (ver ADR-013, actualización
    2026-08-14). Sin `created_by_user_id`: se conserva el del alta."""

    override_id: uuid.UUID
    operador_ausente_id: uuid.UUID
    operador_reemplazante_id: uuid.UUID
    desde: date
    hasta: date
    slot_ids: list[uuid.UUID] | None
    """`None` = alcance TOTAL; lista vacía o con ids = alcance por franja puntual."""
    motivo: str | None


@dataclass(frozen=True, slots=True)
class AsignacionOverrideDTO:
    id: uuid.UUID
    operador_ausente_id: uuid.UUID
    operador_ausente_nombre: str | None
    operador_reemplazante_id: uuid.UUID
    operador_reemplazante_nombre: str | None
    desde: date
    hasta: date
    alcance_total: bool
    slot_ids: list[uuid.UUID]
    estado: str
    motivo: str | None
    intercambio_id: uuid.UUID | None = None
    """Par de coberturas cruzadas al que pertenece (ADR-026); `None` en una común."""


@dataclass(frozen=True, slots=True)
class IntercambioCommand:
    """Intercambio de turnos (ADR-026): A toma las franjas de B y B las de A
    durante el rango. `slot_ids_a` = franjas de A que pasa a cubrir B (`None`
    = todas); `slot_ids_b`, simétrico. Sirve para alta y edición."""

    operador_a_id: uuid.UUID
    operador_b_id: uuid.UUID
    desde: date
    hasta: date
    slot_ids_a: list[uuid.UUID] | None
    slot_ids_b: list[uuid.UUID] | None
    motivo: str | None
    created_by_user_id: uuid.UUID
    intercambio_id: uuid.UUID | None = None
    """Alta: `None` (se genera). Edición: el id del par a reemplazar in-place."""


@dataclass(frozen=True, slots=True)
class IntercambioDTO:
    intercambio_id: uuid.UUID
    coberturas: list[AsignacionOverrideDTO]
    """Siempre dos: [A ausente → B cubre, B ausente → A cubre]."""

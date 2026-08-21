"""Commands y DTOs del modo vacaciones (grilla variante, ADR-025)."""

import uuid
from dataclasses import dataclass, field
from datetime import date, time

from src.modules.turnos.application.dtos.turno_dtos import OperatorShiftView, ResolvedShiftDTO


@dataclass(frozen=True, slots=True)
class VarianteSlotInput:
    casilla_id: uuid.UUID
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    user_ids: list[uuid.UUID]


@dataclass(frozen=True, slots=True)
class CreateGrillaVarianteCommand:
    motivo: str | None
    origen_texto: str | None
    desde: date
    hasta: date
    slots: list[VarianteSlotInput]
    created_by_user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class UpdateGrillaVarianteCommand:
    """Edición in-place de una variante ACTIVA (mismo `id`, reemplazo completo
    de cabecera + franjas + asignaciones). Sin `created_by_user_id`: se
    conserva el del alta."""

    variante_id: uuid.UUID
    motivo: str | None
    origen_texto: str | None
    desde: date
    hasta: date
    slots: list[VarianteSlotInput]


@dataclass(frozen=True, slots=True)
class AdvertenciaCoberturaDTO:
    """Advertencia no bloqueante (ver `grilla_variante_reglas`). Los campos
    opcionales dependen del `tipo`: HUECO/SIN_OPERADOR llevan casilla+día+horas;
    OPERADOR_AUSENTE lleva user + rango de la ausencia."""

    tipo: str
    casilla_id: uuid.UUID | None = None
    casilla_nombre: str | None = None
    dia_semana: int | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    user_id: uuid.UUID | None = None
    user_name: str | None = None
    detalle: str | None = None
    desde: date | None = None
    hasta: date | None = None


@dataclass(frozen=True, slots=True)
class VarianteSlotDTO:
    id: uuid.UUID
    casilla_id: uuid.UUID
    casilla_nombre: str
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    sort_order: int
    operadores: list[OperatorShiftView]


@dataclass(frozen=True, slots=True)
class GrillaVarianteDTO:
    id: uuid.UUID
    motivo: str | None
    origen_texto: str | None
    desde: date
    hasta: date
    estado: str
    created_by_user_id: uuid.UUID
    slots: list[VarianteSlotDTO]
    advertencias: list[AdvertenciaCoberturaDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class VarianteActivaDTO:
    """Cabecera de la variante vigente hoy, para el badge de la home."""

    id: uuid.UUID
    motivo: str | None
    desde: date
    hasta: date


@dataclass(frozen=True, slots=True)
class CurrentShiftsDTO:
    shifts: list[ResolvedShiftDTO]
    variante_activa: VarianteActivaDTO | None


@dataclass(frozen=True, slots=True)
class PrecargaSlotDTO:
    """Franja titular como punto de partida del editor. `operadores` ya viene
    sin el ausente; `requiere_cobertura=True` marca las franjas que eran suyas
    (huecos a resolver)."""

    casilla_id: uuid.UUID
    casilla_nombre: str
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    sort_order: int
    operadores: list[OperatorShiftView]
    requiere_cobertura: bool


@dataclass(frozen=True, slots=True)
class PrecargaGrillaDTO:
    ausente_user_id: uuid.UUID
    ausente_nombre: str | None
    desde: date
    hasta: date
    slots: list[PrecargaSlotDTO]
    advertencias: list[AdvertenciaCoberturaDTO]
    """Solo OPERADOR_AUSENTE: otros operadores titulares con vacaciones
    aprobadas dentro del rango, para marcarlos en el editor."""

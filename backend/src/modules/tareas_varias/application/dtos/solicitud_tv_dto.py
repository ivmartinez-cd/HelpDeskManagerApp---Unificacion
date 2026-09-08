import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class CrearSolicitudTvRequest:
    id_tecnico: int
    tecnico: str
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str


@dataclass(frozen=True, slots=True)
class CrearSolicitudTvPropiaRequest:
    """Alta por el propio técnico autenticado — `id_tecnico`/`tecnico` no
    viajan del cliente, se resuelven del vínculo Empleado↔Siges del usuario."""

    user_id: uuid.UUID
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str


@dataclass(frozen=True, slots=True)
class CrearSolicitudTvAdminRequest:
    """Alta por un supervisor a nombre de cualquier técnico — nace ya
    APROBADA, no pasa por la cola de pendientes (ver `CrearSolicitudTvAdmin`).
    `id_tecnico`/`tecnico` viajan del cliente, igual que en `guardar_input`
    (no se resuelven en el backend)."""

    id_tecnico: int
    tecnico: str
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str
    resuelta_por_email: str


@dataclass(frozen=True, slots=True)
class ListarSolicitudesTvRequest:
    periodo: int
    estado: str | None = None
    id_tecnico: int | None = None


@dataclass(frozen=True, slots=True)
class ListarSolicitudesTvPropiasRequest:
    user_id: uuid.UUID
    periodo: int
    estado: str | None = None


@dataclass(frozen=True, slots=True)
class DecidirSolicitudTvRequest:
    solicitud_id: uuid.UUID
    decision: str  # "APROBADA" | "RECHAZADA"
    resuelta_por_email: str
    motivo: str | None = None


@dataclass(frozen=True, slots=True)
class SolicitudTvDTO:
    id: uuid.UUID
    id_tecnico: int
    tecnico: str
    periodo: int
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str
    estado: str
    creado_en: datetime
    resuelta_en: datetime | None
    resuelta_por_email: str | None
    motivo_rechazo: str | None

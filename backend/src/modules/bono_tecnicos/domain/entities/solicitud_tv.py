import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from src.modules.bono_tecnicos.domain.errors import CampoRequeridoError


class EstadoSolicitudTv(StrEnum):
    """Reemplaza la carga por Google Form: el técnico envía PENDIENTE, un
    supervisor decide. Solo las APROBADA cuentan como TV del período (ver
    `GetPuntajesPeriodo`, que ya no lee `BonoTecnicoInput.tareas_varias`)."""

    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"


@dataclass(slots=True, eq=False)
class SolicitudTv:
    """Una Tarea Varia solicitada por un técnico — columnas `Técnico`/`Fecha`/
    `Razón Social`/`Sucursal`/`Tarea Realizada` del Sheet legacy. `periodo` no
    se guarda como campo propio: se deriva de `fecha` (única fuente de verdad,
    evita que quede desincronizado del mes real de la tarea); la persistencia
    sí lo desnormaliza como columna para poder filtrar por período en SQL."""

    id: uuid.UUID
    id_tecnico: int
    tecnico: str
    fecha: date
    razon_social: str
    sucursal: str
    tarea_realizada: str
    estado: EstadoSolicitudTv
    creado_en: datetime
    resuelta_en: datetime | None = field(default=None)
    resuelta_por_email: str | None = field(default=None)
    motivo_rechazo: str | None = field(default=None)

    def __post_init__(self) -> None:
        _validar_no_vacio("razon_social", self.razon_social)
        _validar_no_vacio("sucursal", self.sucursal)
        _validar_no_vacio("tarea_realizada", self.tarea_realizada)

    @property
    def periodo(self) -> int:
        return self.fecha.year * 100 + self.fecha.month

    def aprobar(self, resuelta_en: datetime, resuelta_por_email: str) -> None:
        self.estado = EstadoSolicitudTv.APROBADA
        self.resuelta_en = resuelta_en
        self.resuelta_por_email = resuelta_por_email
        self.motivo_rechazo = None

    def rechazar(
        self, resuelta_en: datetime, resuelta_por_email: str, motivo: str | None
    ) -> None:
        self.estado = EstadoSolicitudTv.RECHAZADA
        self.resuelta_en = resuelta_en
        self.resuelta_por_email = resuelta_por_email
        self.motivo_rechazo = motivo

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SolicitudTv) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


def _validar_no_vacio(campo: str, valor: str) -> None:
    if not valor.strip():
        raise CampoRequeridoError(campo)

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetPuntajesPeriodoRequest:
    periodo: int


@dataclass(frozen=True, slots=True)
class PuntajeTecnicoDTO:
    tecnico: str
    id_tecnico: int
    periodo: int
    correctivo: int
    preventivo: int
    inst_des: int
    pre_correctivo: int
    entrega_insumos: int
    dias: float
    tareas_varias: int
    puntaje: float | None
    # None si el técnico no está vinculado a un empleado de Gestión de
    # Personal (`Empleado.siges_empresa_id`) — no hay de dónde sugerir.
    dias_sugeridos: float | None


@dataclass(frozen=True, slots=True)
class GuardarBonoInputRequest:
    id_tecnico: int
    periodo: int
    tecnico: str
    dias: float


@dataclass(frozen=True, slots=True)
class GetMiResumenBonoRequest:
    user_id: uuid.UUID
    periodo: int


@dataclass(frozen=True, slots=True)
class MiResumenBonoDTO:
    """`PuntajeTecnicoDTO` del técnico autenticado + el desglose de sus TV
    por estado (`PuntajeTecnicoDTO.tareas_varias` solo cuenta las APROBADA,
    que es lo único que impacta el Puntaje)."""

    tecnico: str
    id_tecnico: int
    periodo: int
    correctivo: int
    preventivo: int
    inst_des: int
    pre_correctivo: int
    entrega_insumos: int
    dias: float
    puntaje: float | None
    dias_sugeridos: float | None
    tv_aprobadas: int
    tv_pendientes: int
    tv_rechazadas: int

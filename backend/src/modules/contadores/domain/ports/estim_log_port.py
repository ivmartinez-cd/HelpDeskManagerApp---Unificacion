from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class EntradaEstimLog:
    """Un registro de auditoría (REGLAS_DE_NEGOCIO §11) — append-only, se
    inserta una fila por cada acción del operador sobre una fila del
    tablero, nunca se pisa ni se borra."""

    operador_user_id: UUID | None
    operador_email: str
    id_maquina: int
    clase: str
    accion: str
    fecha_objetivo: date | None = None
    nro_proceso: int | None = None
    contador_anterior: float | None = None
    contador_propuesto: float | None = None
    tipo_toma_grabado: int | None = None
    fuente: str | None = None
    metodo_detalle: str | None = None
    observacion: str | None = None
    detalle: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResumenAuditoriaMaquina:
    """Lo que el export necesita del historial de un equipo (REGLAS_DE_NEGOCIO
    §12): la observación manual más reciente y un identificador corto de la
    última entrada del log, para que un reclamo de facturación lleve a la
    decisión completa. Solo existe para equipos que el operador tocó."""

    id_log_corto: str
    observacion_manual: str | None


class EstimLogPort(Protocol):
    async def registrar(self, entrada: EntradaEstimLog) -> None: ...

    async def resumen_por_maquina(
        self, nro_proceso: int
    ) -> dict[int, ResumenAuditoriaMaquina]: ...

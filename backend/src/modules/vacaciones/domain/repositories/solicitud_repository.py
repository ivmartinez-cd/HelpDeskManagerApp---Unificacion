import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud, Solicitud


@dataclass(frozen=True, slots=True)
class FiltrosSolicitudes:
    status: EstadoSolicitud | None = None
    empleado_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


@dataclass(frozen=True, slots=True)
class RangoSolapado:
    """Consulta de solape: solicitudes activas (PENDING|APPROVED) que tocan
    [start, end], opcionalmente excluyendo una solicitud (edición)."""

    start: date
    end: date
    excluir_solicitud_id: uuid.UUID | None = None


class SolicitudRepository(Protocol):
    async def get_by_id(self, solicitud_id: uuid.UUID) -> Solicitud | None: ...

    async def list_filtradas(self, filtros: FiltrosSolicitudes) -> list[Solicitud]: ...

    async def list_activas_de_empleado(
        self, empleado_id: uuid.UUID, excluir_solicitud_id: uuid.UUID | None = None
    ) -> list[Solicitud]: ...

    async def list_activas_de_empleados(
        self, empleado_ids: list[uuid.UUID]
    ) -> list[Solicitud]:
        """Todas las activas de un conjunto de empleados (cálculo batch de
        saldos y del 'restante' del calendario, sin N+1)."""
        ...

    async def list_activas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], rango: RangoSolapado
    ) -> list[Solicitud]: ...

    async def list_rangos_activos_por_cargo(
        self, cargo_id: uuid.UUID, excluir_empleado_id: uuid.UUID, rango: RangoSolapado
    ) -> list[tuple[date, date]]:
        """Rangos de solicitudes activas de OTROS empleados ACTIVOS del mismo
        cargo que solapan el rango (validación de límite por cargo)."""
        ...

    async def list_activas_solapadas_de_departamento(
        self, department_id: uuid.UUID, rango: RangoSolapado
    ) -> list[Solicitud]: ...

    async def list_activas_en_rango(
        self, desde: date | None, hasta: date | None, department_id: uuid.UUID | None
    ) -> list[Solicitud]:
        """Eventos del calendario: activas con start_date dentro del rango,
        opcionalmente acotadas a un sector (jefe)."""
        ...

    async def add(self, solicitud: Solicitud) -> None: ...

    async def save(self, solicitud: Solicitud) -> None: ...

    async def delete(self, solicitud_id: uuid.UUID) -> None: ...

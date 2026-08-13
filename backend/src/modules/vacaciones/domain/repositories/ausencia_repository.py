import uuid
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud


@dataclass(frozen=True, slots=True)
class FiltrosAusencias:
    status: EstadoSolicitud | None = None
    tipo: TipoAusencia | None = None
    empleado_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


class AusenciaRepository(Protocol):
    async def get_by_id(self, ausencia_id: uuid.UUID) -> Ausencia | None: ...

    async def list_filtradas(self, filtros: FiltrosAusencias) -> list[Ausencia]: ...

    async def existe_activa_solapada(
        self,
        empleado_id: uuid.UUID,
        tipo: TipoAusencia,
        start: date,
        end: date,
        excluir_ausencia_id: uuid.UUID | None = None,
    ) -> bool:
        """¿Hay otra baja del mismo tipo (PENDING/APPROVED) solapada?
        (paridad con assertNoOverlap del legacy)."""
        ...

    async def list_aprobadas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], start: date, end: date
    ) -> list[Ausencia]:
        """Bajas APPROVED de esos empleados que tocan el rango (reportes)."""
        ...

    async def add(self, ausencia: Ausencia) -> None: ...

    async def save(self, ausencia: Ausencia) -> None: ...

    async def delete(self, ausencia_id: uuid.UUID) -> None: ...

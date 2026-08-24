import uuid
from typing import Protocol

from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class SolicitudTvRepository(Protocol):
    """Persistencia propia (Postgres) de las solicitudes de TV — reemplaza el
    Sheet legacy que alimentaba `Lista!$J$7` a mano."""

    async def add(self, solicitud: SolicitudTv) -> None: ...

    async def get_by_id(self, solicitud_id: uuid.UUID) -> SolicitudTv | None: ...

    async def save(self, solicitud: SolicitudTv) -> None: ...

    async def list_by_periodo(
        self,
        periodo: Periodo,
        *,
        estado: EstadoSolicitudTv | None = None,
        id_tecnico: int | None = None,
    ) -> list[SolicitudTv]: ...

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        """Cantidad de solicitudes APROBADA del período, agrupadas por
        `id_tecnico` — el TV que entra al cálculo de Puntaje
        (`GetPuntajesPeriodo`), ya no un valor cargado a mano."""
        ...

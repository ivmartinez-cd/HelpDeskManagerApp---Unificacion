import uuid
from typing import Protocol

from src.modules.tareas_varias.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.tareas_varias.domain.value_objects.conteo_tv import ConteoTv
from src.modules.tareas_varias.domain.value_objects.periodo import Periodo


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

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        """Solicitudes creadas vs. APROBADA de los 12 meses del año,
        agrupadas por `(id_tecnico, periodo)` — la evolución anual necesita
        ambas series, no solo las aprobadas del mes actual."""
        ...

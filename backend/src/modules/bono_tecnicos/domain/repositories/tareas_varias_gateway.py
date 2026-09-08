from typing import Protocol

from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv, ResumenTvTecnico
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class TareasVariasGateway(Protocol):
    """Lee el conteo de Tareas Varias (`SolicitudTv`, módulo `tareas_varias`)
    para el cálculo de Puntaje, la evolución anual y "Mi bono" — dependencia
    cross-module a propósito, solo en infrastructure (nunca en domain/
    application de bono_tecnicos), mismo criterio que
    `dias_sugeridos_gateway`/`tecnico_identity_gateway`."""

    async def count_aprobadas_por_tecnico(self, periodo: Periodo) -> dict[int, int]:
        """Cantidad de TV APROBADA del período, agrupadas por `id_tecnico` —
        lo que entra al cálculo de Puntaje (`GetPuntajesPeriodo`)."""
        ...

    async def contar_por_tecnico_y_periodo(self, anio: int) -> dict[tuple[int, int], ConteoTv]:
        """TV creadas vs. APROBADA de los 12 meses del año, agrupadas por
        `(id_tecnico, periodo)` — para la evolución anual."""
        ...

    async def resumen_tecnico(self, periodo: Periodo, id_tecnico: int) -> ResumenTvTecnico:
        """Desglose de TV por estado de un técnico en un período — para "Mi
        bono" (`GetMiResumenBono`)."""
        ...

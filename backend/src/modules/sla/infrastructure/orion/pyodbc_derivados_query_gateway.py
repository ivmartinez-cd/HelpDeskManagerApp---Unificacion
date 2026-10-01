from datetime import date

from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado
from src.modules.sla.infrastructure.orion.derivados_query import INCIDENTES_DERIVADOS_SQL
from src.modules.sla.infrastructure.orion.derivados_row_mapping import map_row
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner


class PyodbcDerivadosQueryGateway:
    def __init__(self, runner: OrionQueryRunner, id_mesa_ayuda: int) -> None:
        self._runner = runner
        self._id_mesa_ayuda = id_mesa_ayuda

    async def find_incidentes_derivados(
        self, desde: date, hasta: date
    ) -> list[IncidenteDerivado]:
        rows = await self._runner.fetch_all(
            INCIDENTES_DERIVADOS_SQL,
            (self._id_mesa_ayuda, desde, hasta),
            gateway="derivados",
            log_message="Falló la consulta de incidentes Derivados contra Siges/ORION",
            log_extra={"desde": str(desde), "hasta": str(hasta)},
            error_message="No se pudo consultar la base Siges (ORION)",
        )
        return [map_row(row) for row in rows]

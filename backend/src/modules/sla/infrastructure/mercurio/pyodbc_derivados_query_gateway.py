from datetime import date

from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado
from src.modules.sla.infrastructure.mercurio.derivados_query import INCIDENTES_DERIVADOS_SQL
from src.modules.sla.infrastructure.mercurio.derivados_row_mapping import map_row
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcDerivadosQueryGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_incidentes_derivados(
        self, desde: date, hasta: date
    ) -> list[IncidenteDerivado]:
        rows = await self._runner.fetch_all(
            INCIDENTES_DERIVADOS_SQL,
            (desde, hasta),
            gateway="derivados",
            log_message="Falló la consulta de incidentes Derivados contra Siges/MERCURIO",
            log_extra={"desde": str(desde), "hasta": str(hasta)},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return [map_row(row) for row in rows]

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.infrastructure.orion.pendientes_query import INCIDENTES_SIN_CERRAR_SQL
from src.modules.sla.infrastructure.orion.pendientes_row_mapping import map_row
from src.shared.infrastructure.orion.query_runner import OrionQueryRunner


class PyodbcPendientesQueryGateway:
    def __init__(self, runner: OrionQueryRunner) -> None:
        self._runner = runner

    async def find_incidentes_sin_cerrar(self, meses_corte: int) -> list[IncidenteSinCerrar]:
        rows = await self._runner.fetch_all(
            INCIDENTES_SIN_CERRAR_SQL,
            (meses_corte,),
            gateway="pendientes",
            log_message="Falló la consulta de pendientes a cerrar contra Siges/ORION",
            log_extra={"meses_corte": meses_corte},
            error_message="No se pudo consultar la base Siges (ORION): {exc}",
        )
        return [map_row(row) for row in rows]

from src.modules.sla.domain.entities.incidente_sin_cerrar import IncidenteSinCerrar
from src.modules.sla.infrastructure.mercurio.pendientes_query import INCIDENTES_SIN_CERRAR_SQL
from src.modules.sla.infrastructure.mercurio.pendientes_row_mapping import map_row
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcPendientesQueryGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_incidentes_sin_cerrar(self, meses_corte: int) -> list[IncidenteSinCerrar]:
        rows = await self._runner.fetch_all(
            INCIDENTES_SIN_CERRAR_SQL,
            (meses_corte,),
            gateway="pendientes",
            log_message="Falló la consulta de pendientes a cerrar contra Siges/MERCURIO",
            log_extra={"meses_corte": meses_corte},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return [map_row(row) for row in rows]

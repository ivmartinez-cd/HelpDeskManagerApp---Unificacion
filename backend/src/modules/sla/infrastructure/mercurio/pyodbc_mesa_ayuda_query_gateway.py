from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda
from src.modules.sla.infrastructure.mercurio.mesa_ayuda_query import INCIDENTES_MESA_AYUDA_SQL
from src.modules.sla.infrastructure.mercurio.mesa_ayuda_row_mapping import map_row
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcMesaAyudaQueryGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_incidentes_mesa_ayuda(self, id_tecnico: int) -> list[IncidenteMesaAyuda]:
        rows = await self._runner.fetch_all(
            INCIDENTES_MESA_AYUDA_SQL,
            (id_tecnico,),
            gateway="mesa-ayuda",
            log_message="Falló la consulta de incidentes de Mesa de Ayuda contra Siges/MERCURIO",
            log_extra={"id_tecnico": id_tecnico},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return [map_row(row) for row in rows]

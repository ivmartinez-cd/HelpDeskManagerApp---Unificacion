"""Adapter pyodbc del puerto SlaQueryGateway — consulta en vivo a Siges.

La plomería pyodbc (thread, conexión efímera, timeouts, semáforo de
concurrencia, traducción de errores) vive en el `MercurioQueryRunner`
compartido (ADR-018); acá quedan el SQL, el mapeo de filas y el contexto de
error propios de sla."""

from datetime import timedelta

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.value_objects.periodo import Periodo
from src.modules.sla.infrastructure.mercurio.query import INCIDENTES_SLA_SQL
from src.modules.sla.infrastructure.mercurio.row_mapping import map_row
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcSlaQueryGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_incidentes(self, periodo: Periodo) -> list[IncidenteSla]:
        # FechaOperativo es datetime: BETWEEN hasta el último día a las 00:00
        # dejaría afuera ese día entero. El límite superior es el día siguiente
        # (inclusive a medianoche exacta), y cualquier fila de ese día extra la
        # descarta igual el filtro por período de la propia consulta.
        desde = periodo.primer_dia
        hasta_exclusivo = periodo.ultimo_dia + timedelta(days=1)
        rows = await self._runner.fetch_all(
            INCIDENTES_SLA_SQL,
            (desde, hasta_exclusivo, periodo.value),
            gateway="sla",
            log_message="Fallo la consulta de SLA contra Siges/MERCURIO",
            log_extra={"periodo": periodo.value},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return [map_row(row) for row in rows]

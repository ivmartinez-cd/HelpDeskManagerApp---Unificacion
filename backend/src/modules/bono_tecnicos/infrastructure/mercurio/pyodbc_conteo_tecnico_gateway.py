"""Adapter pyodbc de los puertos ConteoTecnicoGateway/IncidenteTecnicoGateway
— consulta en vivo a Siges.

La plomería pyodbc (thread, conexión efímera, timeouts, semáforo de
concurrencia, traducción de errores) vive en el `MercurioQueryRunner`
compartido (ADR-018); acá quedan el SQL, el mapeo de filas y el contexto de
error propios de bono_tecnicos."""

from datetime import date, timedelta

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.bono_tecnicos.infrastructure.mercurio.incidentes_query import (
    INCIDENTES_TECNICO_SQL,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.incidentes_row_mapping import (
    map_row as map_incidente_row,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.query import CONTEOS_TECNICOS_SQL
from src.modules.bono_tecnicos.infrastructure.mercurio.row_mapping import (
    map_row,
    pivot_conteos,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcConteoTecnicoGateway:
    def __init__(self, runner: MercurioQueryRunner) -> None:
        self._runner = runner

    async def find_conteos(self, periodo: Periodo) -> list[ConteoTecnico]:
        desde, hasta_exclusivo = _rango_fechas(periodo)
        rows = await self._runner.fetch_all(
            CONTEOS_TECNICOS_SQL,
            (desde, hasta_exclusivo, periodo.value),
            gateway="bono_tecnicos",
            log_message="Fallo la consulta de conteos de bono de técnicos contra Siges/MERCURIO",
            log_extra={"periodo": periodo.value},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return pivot_conteos([map_row(row) for row in rows], periodo.value)

    async def find_incidentes(self, periodo: Periodo, id_tecnico: int) -> list[IncidenteBono]:
        desde, hasta_exclusivo = _rango_fechas(periodo)
        rows = await self._runner.fetch_all(
            INCIDENTES_TECNICO_SQL,
            (id_tecnico, desde, hasta_exclusivo, periodo.value),
            gateway="bono_tecnicos",
            log_message="Fallo la consulta de incidentes de bono de técnicos contra Siges/MERCURIO",
            log_extra={"periodo": periodo.value, "id_tecnico": id_tecnico},
            error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
        )
        return [map_incidente_row(row) for row in rows]


def _rango_fechas(periodo: Periodo) -> tuple[date, date]:
    # FechaOperativo es datetime: BETWEEN hasta el último día a las 00:00
    # dejaría afuera ese día entero. El límite superior es el día siguiente
    # (inclusive a medianoche exacta), y cualquier fila de ese día extra la
    # descarta igual el filtro por período de la propia consulta (mismo
    # criterio que sla/PyodbcSlaQueryGateway).
    return periodo.primer_dia, periodo.ultimo_dia + timedelta(days=1)

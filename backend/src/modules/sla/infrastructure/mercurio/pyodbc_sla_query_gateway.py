"""Adapter pyodbc del puerto SlaQueryGateway — consulta en vivo a Siges.

pyodbc es síncrono: la consulta corre en un thread (`asyncio.to_thread`) para
no bloquear el event loop. Conexión nueva por consulta a propósito: es un
fetch esporádico de dashboard, no un hot path, y una conexión efímera es
resiliente a cortes de red/reinicios de MERCURIO sin manejar pooling propio
(las conexiones pyodbc no son thread-safe para compartir entre requests)."""

import asyncio
import logging
from datetime import date, timedelta
from typing import Any

import pyodbc

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.value_objects.periodo import Periodo
from src.modules.sla.infrastructure.mercurio.query import INCIDENTES_SLA_SQL
from src.modules.sla.infrastructure.mercurio.row_mapping import map_row
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class PyodbcSlaQueryGateway:
    def __init__(self, connection_string: str, timeout_seconds: float) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds

    async def find_incidentes(self, periodo: Periodo) -> list[IncidenteSla]:
        # FechaOperativo es datetime: BETWEEN hasta el último día a las 00:00
        # dejaría afuera ese día entero. El límite superior es el día siguiente
        # (inclusive a medianoche exacta), y cualquier fila de ese día extra la
        # descarta igual el filtro por período de la propia consulta.
        desde = periodo.primer_dia
        hasta_exclusivo = periodo.ultimo_dia + timedelta(days=1)
        try:
            rows = await asyncio.to_thread(self._query, desde, hasta_exclusivo, periodo.value)
        except pyodbc.Error as exc:
            logger.error(
                "Fallo la consulta de SLA contra Siges/MERCURIO",
                extra={"periodo": periodo.value},
                exc_info=exc,
            )
            raise ExternalServiceError(
                "No se pudo consultar la base Siges (MERCURIO)"
            ) from exc
        return [map_row(row) for row in rows]

    def _query(self, desde: date, hasta: date, periodo: int) -> list[Any]:
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            # `timeout` del connect es solo de login; este es el de la consulta.
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            cursor.execute(INCIDENTES_SLA_SQL, desde, hasta, periodo)
            return list(cursor.fetchall())

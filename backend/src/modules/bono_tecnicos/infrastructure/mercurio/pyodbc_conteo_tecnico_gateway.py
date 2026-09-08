"""Adapter pyodbc de los puertos ConteoTecnicoGateway/IncidenteTecnicoGateway
— consulta en vivo a Siges.

La plomería pyodbc (thread, conexión efímera, timeouts, semáforo de
concurrencia, traducción de errores) vive en el `MercurioQueryRunner`
compartido (ADR-018); acá quedan el SQL, el mapeo de filas y el contexto de
error propios de bono_tecnicos."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.bono_tecnicos.infrastructure.mercurio.incidentes_query import (
    INCIDENTES_TECNICO_SQL,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.incidentes_row_mapping import (
    map_row as map_incidente_row,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.query import (
    CONTEOS_TECNICOS_ANUAL_SQL,
    CONTEOS_TECNICOS_SQL,
)
from src.modules.bono_tecnicos.infrastructure.mercurio.row_mapping import (
    map_row,
    map_row_anual,
    pivot_conteos,
    pivot_conteos_por_periodo,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_ANUAL_CACHE_TTL_SEGUNDOS = 600.0


class PyodbcConteoTecnicoGateway:
    def __init__(
        self,
        runner: MercurioQueryRunner,
        *,
        anual_cache_ttl_seconds: float = _ANUAL_CACHE_TTL_SEGUNDOS,
    ) -> None:
        self._runner = runner
        self._anual_cache_ttl_seconds = anual_cache_ttl_seconds
        self._anual_lock = asyncio.Lock()
        self._anual_cache: dict[int, tuple[datetime, list[ConteoTecnico]]] = {}

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

    async def find_conteos_anio(self, anio: int) -> list[ConteoTecnico]:
        """Cacheado en memoria por año (TTL 10 min): los meses cerrados del
        año no cambian, y así el gerente puede abrir varios técnicos de la
        vista ejecutiva sin repetir la consulta anual completa a Siges."""
        async with self._anual_lock:
            cacheado = self._anual_cache.get(anio)
            if cacheado is not None and _vigente(cacheado[0], self._anual_cache_ttl_seconds):
                return cacheado[1]
            desde = date(anio, 1, 1)
            hasta_exclusivo = date(anio + 1, 1, 1)
            rows = await self._runner.fetch_all(
                CONTEOS_TECNICOS_ANUAL_SQL,
                (desde, hasta_exclusivo),
                gateway="bono_tecnicos",
                log_message=(
                    "Fallo la consulta anual de conteos de bono de técnicos "
                    "contra Siges/MERCURIO"
                ),
                log_extra={"anio": anio},
                error_message="No se pudo consultar la base Siges (MERCURIO): {exc}",
                # Barre los 12 meses del año en un solo round trip: más
                # pesada que la consulta mensual, timeout más holgado.
                timeout_override=90.0,
            )
            conteos = pivot_conteos_por_periodo([map_row_anual(row) for row in rows])
            self._anual_cache[anio] = (datetime.now(UTC), conteos)
            return conteos

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
    # Fecha_Cierre es datetime: BETWEEN hasta el último día a las 00:00
    # dejaría afuera ese día entero. El límite superior es el día siguiente
    # (inclusive a medianoche exacta), y cualquier fila de ese día extra la
    # descarta igual el filtro por período de la propia consulta (mismo
    # criterio que sla/PyodbcSlaQueryGateway).
    return periodo.primer_dia, periodo.ultimo_dia + timedelta(days=1)


def _vigente(consultado_en: datetime, ttl_seconds: float) -> bool:
    return (datetime.now(UTC) - consultado_en).total_seconds() < ttl_seconds

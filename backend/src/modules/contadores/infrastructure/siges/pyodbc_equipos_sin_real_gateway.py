"""Adapter pyodbc del puerto EquiposSinRealPort — consulta en vivo a Siges.

Mismo criterio que PyodbcOperadorGateway (pyodbc síncrono → thread, conexión
efímera por consulta), más una caché TTL en memoria: la consulta recorre
Contadores completo (~10s) y la UI reordena/pagina/filtra sobre el mismo
universo, así que cada interacción no puede costar otra pasada por MERCURIO.
El lock serializa refrescos concurrentes (una sola consulta en vuelo)."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import pyodbc

from src.modules.contadores.domain.entities.equipo_sin_real import (
    EquipoSinReal,
    EquiposSinRealSnapshot,
)
from src.modules.contadores.infrastructure.siges.equipos_sin_real_query import (
    EQUIPOS_SIN_REAL_SQL,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class PyodbcEquiposSinRealGateway:
    def __init__(
        self, connection_string: str, timeout_seconds: float, cache_ttl_seconds: float
    ) -> None:
        self._connection_string = connection_string
        self._timeout_seconds = timeout_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: EquiposSinRealSnapshot | None = None

    async def list_equipos(self, *, force_refresh: bool = False) -> EquiposSinRealSnapshot:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            try:
                rows = await asyncio.to_thread(self._query)
            except pyodbc.Error as exc:
                logger.error(
                    "Fallo la consulta de equipos sin contador real contra Siges/MERCURIO",
                    exc_info=exc,
                )
                raise ExternalServiceError(
                    "No se pudo consultar la base Siges (MERCURIO)"
                ) from exc
            self._snapshot = EquiposSinRealSnapshot(
                equipos=[_to_equipo(row) for row in rows],
                consultado_en=datetime.now(UTC),
            )
            return self._snapshot

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds

    def _query(self) -> list[Any]:
        with pyodbc.connect(
            self._connection_string, timeout=int(self._timeout_seconds)
        ) as connection:
            connection.timeout = int(self._timeout_seconds)
            cursor = connection.cursor()
            cursor.execute(EQUIPOS_SIN_REAL_SQL)
            return list(cursor.fetchall())


def _to_equipo(row: Any) -> EquipoSinReal:
    return EquipoSinReal(
        id_maquina=row.id_maquina,
        id_empresa_cliente=row.id_empresa_cliente,
        serie=row.serie.strip(),
        modelo=row.modelo.strip(),
        tecnologia=row.tecnologia.strip() if row.tecnologia else None,
        propiedad=row.propiedad.strip() if row.propiedad else None,
        cliente=row.cliente.strip(),
        sucursal=row.sucursal.strip(),
        estado_maquina=row.estado_maquina.strip(),
        observaciones=(row.observaciones or "").strip(),
        fecha_ultimo_real=row.ultima_real.date() if row.ultima_real else None,
        fecha_referencia=row.fecha_ref.date(),
        dias_sin_real=row.dias_sin_real,
        meses_sin_real=row.meses_sin_real,
        im1=row.im1,
        im2=row.im2,
        im3=row.im3,
    )

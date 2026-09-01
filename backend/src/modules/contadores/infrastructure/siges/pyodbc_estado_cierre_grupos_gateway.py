"""Adapter pyodbc del puerto EstadoCierreGruposPort — consulta en vivo a
Siges. Mismo esqueleto que `PyodbcAnexosPendientesGateway`: plomería en
`MercurioQueryRunner` (ADR-018), acá solo el parámetro dinámico (mes en
curso) y la caché TTL."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.modules.contadores.domain.entities.estado_cierre_grupo import (
    EstadoCierreGrupo,
    EstadoCierreGruposSnapshot,
)
from src.modules.contadores.domain.services.ciclo_cierre import hoy_argentina
from src.modules.contadores.domain.services.periodos_facturacion import periodo_de
from src.modules.contadores.infrastructure.siges.estado_cierre_grupos_query import (
    ESTADO_CIERRE_GRUPOS_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcEstadoCierreGruposGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: EstadoCierreGruposSnapshot | None = None

    async def list_estado(
        self, *, force_refresh: bool = False
    ) -> EstadoCierreGruposSnapshot:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            rows = await self._runner.fetch_all(
                ESTADO_CIERRE_GRUPOS_SQL,
                (periodo_de(hoy_argentina()),),
                gateway="estado_cierre_grupos",
                log_message=(
                    "Fallo la consulta de estado de cierre por grupo contra Siges/MERCURIO"
                ),
            )
            self._snapshot = EstadoCierreGruposSnapshot(
                grupos=[_to_estado(row) for row in rows],
                consultado_en=datetime.now(UTC),
            )
            return self._snapshot

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds


def _to_estado(row: Any) -> EstadoCierreGrupo:
    return EstadoCierreGrupo(grupo=row.grupo.strip(), sin_cerrar=bool(row.sin_cerrar))

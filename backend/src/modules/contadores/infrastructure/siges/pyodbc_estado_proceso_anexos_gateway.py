"""Adapter pyodbc del puerto EstadoProcesoAnexosPort — consulta en vivo a
Siges. Mismo esqueleto que `PyodbcEstadoCierreGruposGateway` (plomería en
`MercurioQueryRunner`, ADR-018, caché TTL), pero con `_consultar()` extraído:
la query no lleva parámetros, así que `list_estado` no necesita calcular
`hoy` — se mantiene igual de corto sin repetir la deuda de tamaño del
gateway hermano (`scripts/sizes-baseline.json`)."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.modules.contadores.domain.entities.estado_proceso_anexo import (
    EstadoProcesoAnexo,
    EstadoProcesoAnexosSnapshot,
)
from src.modules.contadores.infrastructure.siges.estado_proceso_anexos_query import (
    ESTADO_PROCESO_ANEXOS_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcEstadoProcesoAnexosGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: EstadoProcesoAnexosSnapshot | None = None

    async def list_estado(
        self, *, force_refresh: bool = False
    ) -> EstadoProcesoAnexosSnapshot:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            self._snapshot = await self._consultar()
            return self._snapshot

    async def _consultar(self) -> EstadoProcesoAnexosSnapshot:
        rows = await self._runner.fetch_all(
            ESTADO_PROCESO_ANEXOS_SQL,
            gateway="estado_proceso_anexos",
            log_message=(
                "Fallo la consulta de anexos sin proceso contra Siges/MERCURIO"
            ),
        )
        return EstadoProcesoAnexosSnapshot(
            anexos=[_to_estado(row) for row in rows],
            consultado_en=datetime.now(UTC),
        )

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds


def _to_estado(row: Any) -> EstadoProcesoAnexo:
    ultimo = row.ultimo_periodo_procesado
    return EstadoProcesoAnexo(
        id_anexo=row.id_anexo,
        anexo=(row.anexo or "").strip(),
        grupo=row.grupo.strip(),
        ultimo_periodo_procesado=ultimo.strip() if ultimo else None,
        maquinas_activas=row.maquinas_activas,
    )

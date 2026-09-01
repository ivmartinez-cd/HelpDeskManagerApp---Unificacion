"""Adapter pyodbc del puerto ClientesPendientesPeriodoPort — consulta en vivo
a Siges. Mismo esqueleto que `PyodbcEstadoCierreGruposGateway`: plomería en
`MercurioQueryRunner` (ADR-018), acá el parámetro es el período inmediato
anterior (no el mes en curso) y la caché TTL."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)
from src.modules.contadores.domain.services.ciclo_cierre import hoy_argentina
from src.modules.contadores.domain.services.periodos_facturacion import (
    periodo_anterior,
    periodo_de,
)
from src.modules.contadores.infrastructure.siges.clientes_pendientes_periodo_query import (
    CLIENTES_PENDIENTES_PERIODO_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcClientesPendientesPeriodoGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: ClientesPendientesPeriodo | None = None

    async def contar(
        self, *, force_refresh: bool = False
    ) -> ClientesPendientesPeriodo:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            periodo = periodo_anterior(periodo_de(hoy_argentina()))
            rows = await self._runner.fetch_all(
                CLIENTES_PENDIENTES_PERIODO_SQL,
                (periodo,),
                gateway="clientes_pendientes_periodo",
                log_message=(
                    "Fallo la consulta de clientes pendientes del período anterior "
                    "contra Siges/MERCURIO"
                ),
            )
            self._snapshot = ClientesPendientesPeriodo(
                periodo=periodo,
                grupos=_grupos(rows),
                consultado_en=datetime.now(UTC),
            )
            return self._snapshot

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds


def _grupos(rows: list[Any]) -> tuple[str, ...]:
    return tuple(row.grupo.strip() for row in rows)

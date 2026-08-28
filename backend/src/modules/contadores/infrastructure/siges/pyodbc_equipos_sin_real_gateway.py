"""Adapter pyodbc del puerto EquiposSinRealPort — consulta en vivo a Siges.

La plomería pyodbc vive en el `MercurioQueryRunner` compartido (ADR-018); acá
quedan los casos especiales propios de esta consulta: recorre Contadores
completo (~10 s), así que tiene timeout propio (120 s, vía `timeout_override`)
y una caché TTL en memoria — la UI reordena/pagina/filtra sobre el mismo
universo y cada interacción no puede costar otra pasada por MERCURIO. El lock
serializa refrescos concurrentes (una sola consulta en vuelo)."""

import asyncio
from datetime import UTC, datetime
from typing import Any

from src.modules.contadores.domain.entities.equipo_sin_real import (
    EquipoSinReal,
    EquiposSinRealSnapshot,
)
from src.modules.contadores.infrastructure.siges.equipos_sin_real_query import (
    EQUIPOS_SIN_REAL_SQL,
    PARQUE_ELEGIBLE_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcEquiposSinRealGateway:
    def __init__(
        self, runner: MercurioQueryRunner, timeout_seconds: float, cache_ttl_seconds: float
    ) -> None:
        self._runner = runner
        self._timeout_seconds = timeout_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: EquiposSinRealSnapshot | None = None
        # Snapshot independiente: mismo criterio de caché, pero otra consulta
        # (parque elegible completo, no solo "sin real") — no comparten TTL
        # ni se refrescan juntos.
        self._parque_lock = asyncio.Lock()
        self._parque: dict[int, int] | None = None
        self._parque_consultado_en: datetime | None = None

    async def list_equipos(self, *, force_refresh: bool = False) -> EquiposSinRealSnapshot:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            rows = await self._runner.fetch_all(
                EQUIPOS_SIN_REAL_SQL,
                gateway="equipos_sin_real",
                log_message=(
                    "Fallo la consulta de equipos sin contador real contra Siges/MERCURIO"
                ),
                timeout_override=self._timeout_seconds,
            )
            self._snapshot = EquiposSinRealSnapshot(
                equipos=[_to_equipo(row) for row in rows],
                consultado_en=datetime.now(UTC),
            )
            return self._snapshot

    async def parque_elegible_por_empresa(
        self, *, force_refresh: bool = False
    ) -> dict[int, int]:
        async with self._parque_lock:
            if not force_refresh and self._parque_vigente():
                assert self._parque is not None
                return self._parque
            rows = await self._runner.fetch_all(
                PARQUE_ELEGIBLE_SQL,
                gateway="equipos_sin_real",
                log_message="Fallo el conteo de parque elegible contra Siges/MERCURIO",
                timeout_override=self._timeout_seconds,
            )
            self._parque = {int(row.id_empresa): int(row.cantidad) for row in rows}
            self._parque_consultado_en = datetime.now(UTC)
            return self._parque

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds

    def _parque_vigente(self) -> bool:
        if self._parque is None or self._parque_consultado_en is None:
            return False
        edad = (datetime.now(UTC) - self._parque_consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds


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

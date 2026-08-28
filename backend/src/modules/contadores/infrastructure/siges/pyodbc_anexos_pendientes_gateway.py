"""Adapter pyodbc del puerto AnexosPendientesPort — consulta en vivo a Siges.

Mismo esqueleto que `PyodbcEquiposSinRealGateway`: la plomería vive en el
`MercurioQueryRunner` compartido (ADR-018) y acá quedan los parámetros
dinámicos (el corte de período — ahora inclusivo del mes en curso, ver
`anexos_pendientes_query.py` — y la ventana de recencia de 12 meses ruedan
solos con el calendario — el "más dinámico" pedido sobre el legacy, que los
tomaba de un formulario) y la caché TTL: la UI reordena/filtra sobre el
mismo universo sin otra pasada por MERCURIO."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from src.modules.contadores.domain.entities.anexo_pendiente import (
    AnexoPendiente,
    AnexosPendientesSnapshot,
)
from src.modules.contadores.domain.services.periodos_facturacion import (
    periodo_de,
    restar_meses,
)
from src.modules.contadores.infrastructure.siges.anexos_pendientes_query import (
    ANEXOS_PENDIENTES_SQL,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_VENTANA_RECENCIA_MESES = 12


class PyodbcAnexosPendientesGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._snapshot: AnexosPendientesSnapshot | None = None

    async def list_anexos(self, *, force_refresh: bool = False) -> AnexosPendientesSnapshot:
        async with self._lock:
            if not force_refresh and self._snapshot_vigente():
                assert self._snapshot is not None
                return self._snapshot
            hoy = datetime.now(UTC).date()
            rows = await self._runner.fetch_all(
                ANEXOS_PENDIENTES_SQL,
                (periodo_de(hoy), restar_meses(hoy, _VENTANA_RECENCIA_MESES)),
                gateway="anexos_pendientes",
                log_message=(
                    "Fallo la consulta de anexos pendientes de cierre contra Siges/MERCURIO"
                ),
            )
            self._snapshot = AnexosPendientesSnapshot(
                anexos=[_to_anexo(row) for row in rows],
                consultado_en=datetime.now(UTC),
            )
            return self._snapshot

    def _snapshot_vigente(self) -> bool:
        if self._snapshot is None:
            return False
        edad = (datetime.now(UTC) - self._snapshot.consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds


def _limpio(valor: str | None) -> str | None:
    if valor is None:
        return None
    return valor.strip() or None


def _to_anexo(row: Any) -> AnexoPendiente:
    return AnexoPendiente(
        id_anexo=row.id_anexo,
        anexo=row.anexo.strip(),
        grupo=_limpio(row.grupo),
        contrato=_limpio(row.contrato),
        id_empresa_admin=row.id_empresa_admin,
        empresa_admin=_limpio(row.empresa_admin),
        vendedor=_limpio(row.vendedor),
        moneda=_limpio(row.moneda),
        moneda_facturacion=_limpio(row.moneda_facturacion),
        periodo=row.periodo.strip(),
        fecha_proceso=row.fecha_proceso.date(),
        importe_usd=Decimal(row.importe_usd),
    )

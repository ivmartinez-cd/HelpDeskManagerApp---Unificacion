"""Adapter pyodbc del puerto `ClientesNuevosSigesPort` — consulta en vivo a
Siges con caché TTL por consulta (mismo esqueleto que
`PyodbcAnexosPendientesGateway`: la plomería es el `MercurioQueryRunner`
compartido, ADR-018). Las dos consultas son livianas (subconsultas sobre
`MaquinaUFisica`/`Contrato` filtradas por empresa) — alcanza el timeout
general del runner."""

import asyncio
from datetime import UTC, date, datetime
from typing import Any

from src.modules.contadores.domain.entities.cliente_nuevo import (
    CandidatoClienteNuevo,
    ResumenSigesClienteNuevo,
)
from src.modules.contadores.domain.services.rubro_empresa_admin import rubro_por_empresa_admin
from src.modules.contadores.infrastructure.siges.clientes_nuevos_query import (
    CANDIDATOS_SQL,
    build_resumen_instalaciones_sql,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner

_GATEWAY = "clientes_nuevos"


class PyodbcClientesNuevosGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._ttl = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._resumen_cache: dict[frozenset[int], tuple[datetime, dict[int, Any]]] = {}
        self._candidatos_cache: dict[date, tuple[datetime, list[CandidatoClienteNuevo]]] = {}

    async def resumen_por_empresa(
        self, empresa_ids: frozenset[int], *, force_refresh: bool = False
    ) -> dict[int, ResumenSigesClienteNuevo]:
        if not empresa_ids:
            return {}
        async with self._lock:
            cached = self._resumen_cache.get(empresa_ids)
            if cached and not force_refresh and self._vigente(cached[0]):
                return cached[1]
            ids = sorted(empresa_ids)
            rows = await self._runner.fetch_all(
                build_resumen_instalaciones_sql(len(ids)),
                ids,
                gateway=_GATEWAY,
                log_message="Fallo la consulta de instalaciones de clientes nuevos contra Siges",
            )
            resumen = {row.empresa_id: _to_resumen(row) for row in rows}
            self._resumen_cache[empresa_ids] = (datetime.now(UTC), resumen)
            return resumen

    async def candidatos_desde(
        self, firmado_desde: date, *, force_refresh: bool = False
    ) -> list[CandidatoClienteNuevo]:
        async with self._lock:
            cached = self._candidatos_cache.get(firmado_desde)
            if cached and not force_refresh and self._vigente(cached[0]):
                return cached[1]
            rows = await self._runner.fetch_all(
                CANDIDATOS_SQL,
                (firmado_desde, firmado_desde),
                gateway=_GATEWAY,
                log_message="Fallo la consulta de candidatos a cliente nuevo contra Siges",
            )
            candidatos = _primer_contrato_por_empresa(rows)
            self._candidatos_cache[firmado_desde] = (datetime.now(UTC), candidatos)
            return candidatos

    def _vigente(self, consultado_en: datetime) -> bool:
        return (datetime.now(UTC) - consultado_en).total_seconds() < self._ttl


def _primer_contrato_por_empresa(rows: list[Any]) -> list[CandidatoClienteNuevo]:
    # Las filas vienen por firma ascendente: la primera de cada empresa es su
    # primer contrato. Se devuelven de la más reciente a la más vieja.
    vistos: dict[int, CandidatoClienteNuevo] = {}
    for row in rows:
        if row.empresa_id not in vistos:
            vistos[row.empresa_id] = _to_candidato(row)
    return sorted(vistos.values(), key=lambda c: c.fecha_firma or date.min, reverse=True)


def _fecha(valor: Any) -> date | None:
    if valor is None:
        return None
    return valor.date() if isinstance(valor, datetime) else valor


def _limpio(valor: str | None) -> str | None:
    if valor is None:
        return None
    return valor.strip() or None


def _to_resumen(row: Any) -> ResumenSigesClienteNuevo:
    return ResumenSigesClienteNuevo(
        empresa_id=row.empresa_id,
        equipos_instalados=row.equipos_instalados or 0,
        instalas=row.instalas or 0,
        primera_instalacion=_fecha(row.primera_instalacion),
        ultima_instalacion=_fecha(row.ultima_instalacion),
        equipos_con_toma=row.equipos_con_toma or 0,
        contrato_nro=_limpio(row.contrato_nro),
        fecha_firma=_fecha(row.fecha_firma),
        vendedor=_limpio(row.vendedor),
        rubro=rubro_por_empresa_admin(row.id_empresa_admin),
    )


def _to_candidato(row: Any) -> CandidatoClienteNuevo:
    return CandidatoClienteNuevo(
        empresa_id=row.empresa_id,
        cliente=(row.cliente or "").strip(),
        contrato_nro=_limpio(row.contrato_nro),
        fecha_firma=_fecha(row.fecha_firma),
        vendedor=_limpio(row.vendedor),
        rubro=rubro_por_empresa_admin(row.id_empresa_admin),
        equipos_instalados=row.equipos_instalados or 0,
    )

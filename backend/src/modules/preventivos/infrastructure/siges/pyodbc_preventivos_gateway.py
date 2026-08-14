"""Adapter pyodbc del puerto PreventivosQueryGateway — consulta en vivo a
Siges vía el runner compartido (ADR-018; nada de plomería propia). La consulta
por zona es liviana (0.2-0.4 s medidos), pero la UI pagina/filtra/reordena
sobre el mismo universo: una caché TTL corta por zona evita pagar una pasada
por MERCURIO en cada interacción, y su `consultado_en` alimenta el sello de
frescura de la pantalla. El lock serializa refrescos concurrentes."""

import asyncio
from datetime import UTC, datetime

from src.modules.preventivos.domain.entities.equipo_preventivo import ParqueZonaSnapshot
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque
from src.modules.preventivos.infrastructure.siges.query import PARQUE_ZONA_SQL, ZONAS_SQL
from src.modules.preventivos.infrastructure.siges.row_mapping import (
    map_equipo_row,
    map_zona_row,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcPreventivosGateway:
    def __init__(self, runner: MercurioQueryRunner, cache_ttl_seconds: float) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        self._lock = asyncio.Lock()
        self._por_zona: dict[str, ParqueZonaSnapshot] = {}
        self._zonas: list[ZonaParque] | None = None
        self._zonas_consultadas_en: datetime | None = None

    async def list_equipos_por_zona(
        self, zona: str, *, force_refresh: bool = False
    ) -> ParqueZonaSnapshot:
        async with self._lock:
            vigente = self._por_zona.get(zona)
            if not force_refresh and vigente is not None and self._es_vigente(
                vigente.consultado_en
            ):
                return vigente
            rows = await self._runner.fetch_all(
                PARQUE_ZONA_SQL,
                (zona,),
                gateway="preventivos_parque_zona",
                log_message="Falló la consulta del parque de preventivos contra Siges/MERCURIO",
                log_extra={"zona": zona},
            )
            snapshot = ParqueZonaSnapshot(
                equipos=tuple(map_equipo_row(row) for row in rows),
                consultado_en=datetime.now(UTC),
            )
            self._por_zona[zona] = snapshot
            return snapshot

    async def list_zonas(self) -> list[ZonaParque]:
        async with self._lock:
            if self._zonas is not None and self._es_vigente(self._zonas_consultadas_en):
                return self._zonas
            rows = await self._runner.fetch_all(
                ZONAS_SQL,
                gateway="preventivos_zonas",
                log_message="Falló el catálogo de zonas de preventivos contra Siges/MERCURIO",
            )
            self._zonas = [map_zona_row(row) for row in rows]
            self._zonas_consultadas_en = datetime.now(UTC)
            return self._zonas

    def _es_vigente(self, consultado_en: datetime | None) -> bool:
        if consultado_en is None:
            return False
        edad = (datetime.now(UTC) - consultado_en).total_seconds()
        return edad < self._cache_ttl_seconds

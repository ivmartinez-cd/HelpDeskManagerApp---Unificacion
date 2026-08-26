"""Adapter pyodbc del puerto PreventivosQueryGateway — consulta en vivo a
Siges vía el runner compartido (ADR-018; nada de plomería propia). Medido en
frío 2026-08-26 contra el backend real: ZONAS_SQL 5.2 s, PARQUE_ZONA_SQL
4.5 s (los `_ACTIVIDAD_EMPRESA_JOIN`/`_EMPRESA_VIVA_WHERE` de query.py barren
`Contadores`/`Incidente` completas, sin filtrar por zona) — muy por encima
del 0.2-0.4 s que este módulo asumía. La UI pagina/filtra/reordena sobre el
mismo universo: una caché TTL evita pagar una pasada por MERCURIO en cada
interacción, y su `consultado_en` alimenta el sello de frescura de la
pantalla. El catálogo de zonas cambia mucho menos seguido que el parque de
una zona puntual (es un conteo agregado, no el estado operativo que un
usuario habilita/deshabilita) — tiene su propio TTL, más largo, para que la
consulta cara de arriba se pague con menos frecuencia. El lock serializa
refrescos concurrentes."""

import asyncio
from datetime import UTC, datetime

from src.modules.preventivos.domain.entities.equipo_preventivo import ParqueZonaSnapshot
from src.modules.preventivos.domain.entities.sucursal_coordenadas import (
    SucursalParaGeocoding,
)
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque
from src.modules.preventivos.infrastructure.siges.query import (
    PARQUE_ZONA_SQL,
    SUCURSALES_GEOCODING_SQL,
    ZONAS_SQL,
)
from src.modules.preventivos.infrastructure.siges.row_mapping import (
    map_equipo_row,
    map_sucursal_geocoding_row,
    map_zona_row,
)
from src.shared.infrastructure.mercurio.query_runner import MercurioQueryRunner


class PyodbcPreventivosGateway:
    def __init__(
        self,
        runner: MercurioQueryRunner,
        cache_ttl_seconds: float,
        meses_actividad: int,
        zonas_cache_ttl_seconds: float | None = None,
    ) -> None:
        self._runner = runner
        self._cache_ttl_seconds = cache_ttl_seconds
        # Por defecto, igual al TTL general — quien arma el gateway (ver
        # presentation/dependencies.py) le pasa uno más largo a propósito.
        self._zonas_cache_ttl_seconds = (
            zonas_cache_ttl_seconds if zonas_cache_ttl_seconds is not None else cache_ttl_seconds
        )
        self._meses_actividad = meses_actividad
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
                (self._meses_actividad, self._meses_actividad, zona),
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
            if self._zonas is not None and self._es_vigente(
                self._zonas_consultadas_en, ttl=self._zonas_cache_ttl_seconds
            ):
                return self._zonas
            rows = await self._runner.fetch_all(
                ZONAS_SQL,
                (self._meses_actividad, self._meses_actividad),
                gateway="preventivos_zonas",
                log_message="Falló el catálogo de zonas de preventivos contra Siges/MERCURIO",
            )
            self._zonas = [map_zona_row(row) for row in rows]
            self._zonas_consultadas_en = datetime.now(UTC)
            return self._zonas

    async def list_sucursales_para_geocoding(self) -> list[SucursalParaGeocoding]:
        # Sin cache: la geocodificación se dispara a mano, de vez en cuando —
        # no es una interacción de UI que se repita en cada click.
        rows = await self._runner.fetch_all(
            SUCURSALES_GEOCODING_SQL,
            (self._meses_actividad, self._meses_actividad),
            gateway="preventivos_sucursales_geocoding",
            log_message="Falló la consulta de sucursales para geocoding contra Siges/MERCURIO",
        )
        return [map_sucursal_geocoding_row(row) for row in rows]

    def _es_vigente(self, consultado_en: datetime | None, *, ttl: float | None = None) -> bool:
        if consultado_en is None:
            return False
        edad = (datetime.now(UTC) - consultado_en).total_seconds()
        return edad < (ttl if ttl is not None else self._cache_ttl_seconds)

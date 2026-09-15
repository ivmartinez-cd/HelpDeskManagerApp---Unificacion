"""Implementación Postgres del puerto CotizacionDolarRepository (tabla
cotizaciones_dolar)."""

from datetime import UTC, date, datetime

from sqlalchemy.dialects.postgresql import Insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.domain.repositories.cotizacion_dolar_repository import (
    CotizacionDolar,
)
from src.modules.liquidaciones.infrastructure.models.cotizacion_dolar_model import (
    CotizacionDolarModel,
)


class SqlAlchemyCotizacionDolarRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_periodo(self, periodo: str) -> CotizacionDolar | None:
        row = await self._session.get(CotizacionDolarModel, periodo)
        return _to_entity(row) if row else None

    async def upsert(
        self,
        periodo: str,
        compra: float,
        venta: float,
        fecha_cotizacion: date,
        fuente: str,
    ) -> None:
        stmt = _upsert_stmt(periodo, compra, venta, fecha_cotizacion, fuente)
        await self._session.execute(stmt)


def _upsert_stmt(
    periodo: str, compra: float, venta: float, fecha_cotizacion: date, fuente: str
) -> Insert:
    stmt = pg_insert(CotizacionDolarModel).values(
        periodo=periodo, compra=compra, venta=venta,
        fecha_cotizacion=fecha_cotizacion, fuente=fuente, updated_at=datetime.now(UTC),
    )
    return stmt.on_conflict_do_update(
        index_elements=[CotizacionDolarModel.periodo],
        set_={
            "compra": stmt.excluded.compra,
            "venta": stmt.excluded.venta,
            "fecha_cotizacion": stmt.excluded.fecha_cotizacion,
            "fuente": stmt.excluded.fuente,
            "updated_at": stmt.excluded.updated_at,
        },
    )


def _to_entity(row: CotizacionDolarModel) -> CotizacionDolar:
    return CotizacionDolar(
        periodo=row.periodo,
        compra=row.compra,
        venta=row.venta,
        fecha_cotizacion=row.fecha_cotizacion,
        fuente=row.fuente,
        updated_at=row.updated_at,
    )

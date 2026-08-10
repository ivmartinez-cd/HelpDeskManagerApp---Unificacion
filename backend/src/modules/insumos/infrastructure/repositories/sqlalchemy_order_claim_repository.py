from typing import Any, cast

from sqlalchemy import CursorResult, func, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.order_claim_model import OrderClaimModel


class SqlAlchemyOrderClaimRepository:
    """Implementa el puerto OrderClaimRepository. `try_claim` es un solo
    INSERT atómico contra el índice único parcial (`status='IN_PROGRESS'`)
    — Postgres resuelve la carrera entre dos intentos concurrentes sin
    ningún lock explícito de nuestro lado; el que pierde recibe `rowcount
    == 0`, no una excepción."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def try_claim(self, device_serial: str, sku: str) -> bool:
        stmt = (
            pg_insert(OrderClaimModel)
            .values(device_serial=device_serial, sku=sku)
            .on_conflict_do_nothing(
                index_elements=["device_serial", "sku"],
                # Tiene que ser un literal SQL, no un parámetro bindeado
                # (`OrderClaimModel.status == "IN_PROGRESS"` compila como
                # `$N::VARCHAR`) — Postgres exige que el predicado del
                # ON CONFLICT coincida TEXTUALMENTE con el del índice
                # parcial (ver migración ebe03bf01e96, uq_order_claim_in_progress)
                # o no lo reconoce como constraint válido para el conflicto.
                index_where=text("status = 'IN_PROGRESS'"),
            )
        )
        result = cast(CursorResult[Any], await self._session.execute(stmt))
        await self._session.flush()
        return result.rowcount == 1

    async def release(self, device_serial: str, sku: str) -> None:
        stmt = (
            update(OrderClaimModel)
            .where(
                OrderClaimModel.device_serial == device_serial,
                OrderClaimModel.sku == sku,
                OrderClaimModel.status == "IN_PROGRESS",
            )
            .values(status="DONE", released_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()

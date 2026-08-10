"""Tests de integración de SqlAlchemyRequestValidationRepository (Postgres de test)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.request_validation_model import (
    RequestValidationModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_request_validation_repository import (  # noqa: E501
    SqlAlchemyRequestValidationRepository,
)


def _row(status: str, swap_note: str | None = None) -> RequestValidationModel:
    return RequestValidationModel(
        hp_request_id=974325,
        customer_id=8,
        device_id=7,
        device_serial="SERIE1",
        sku="CF230A",
        initial_percent_left=0.0,
        deadline_at=datetime.now(UTC) + timedelta(hours=6),
        status=status,
        swap_note=swap_note,
        diagnosis_headline="Posible falla de sensor",
    )


async def test_get_pending_devuelve_solo_pending(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestValidationRepository(db_session)
    db_session.add(_row("PENDING"))
    await db_session.flush()

    pending = await repo.get_pending(974325)

    assert pending is not None
    assert pending.initial_percent_left == 0.0
    assert pending.diagnosis_headline == "Posible falla de sensor"


async def test_get_pending_ignora_resueltas(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestValidationRepository(db_session)
    db_session.add(_row("DISMISSED"))
    await db_session.flush()

    assert await repo.get_pending(974325) is None


async def test_get_swap_note_sin_filtrar_por_status(db_session: AsyncSession) -> None:
    """La nota de cambio de insumo se lee al crear el pedido aunque la validación ya
    esté CONFIRMED — va al Historial, nunca al texto del pedido."""
    repo = SqlAlchemyRequestValidationRepository(db_session)
    db_session.add(_row("CONFIRMED", swap_note="Cambio de insumo detectado"))
    await db_session.flush()

    assert await repo.get_swap_note(974325) == "Cambio de insumo detectado"
    assert await repo.get_swap_note(999999) is None

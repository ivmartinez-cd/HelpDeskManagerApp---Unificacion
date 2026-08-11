"""Tests de integración de SqlAlchemyRequestValidationRepository (Postgres de test)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_CONFIRMED,
    VALIDATION_DISMISSED,
    ValidationStart,
)
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


def _start(**overrides: object) -> ValidationStart:
    base: dict[str, object] = {
        "hp_request_id": 974325,
        "customer_id": 8,
        "device_id": 7,
        "device_serial": "SERIE1",
        "sku": "CF230A",
        "initial_percent_left": 0.0,
        "deadline_minutes": 360,
        "swap_note": None,
        "diagnosis_headline": "Posible falla de sensor",
        "diagnosis_detail": "• Sin antecedentes",
    }
    base.update(overrides)
    return ValidationStart(**base)  # type: ignore[arg-type]


async def test_start_crea_la_fila_pending_con_deadline(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestValidationRepository(db_session)

    await repo.start(_start())

    row = await db_session.get(RequestValidationModel, 974325)
    assert row is not None
    assert row.status == "PENDING"
    assert row.swap_checked is True
    assert row.diagnosis_headline == "Posible falla de sensor"
    remaining = row.deadline_at - datetime.now(UTC)
    assert timedelta(hours=5) < remaining <= timedelta(hours=6)
    assert await repo.is_diagnosed(974325) is True
    assert await repo.is_diagnosed(999999) is False


async def test_start_no_reinicia_el_reloj_ni_pisa_un_status_resuelto(
    db_session: AsyncSession,
) -> None:
    """Ver la misma solicitud dos veces no reabre una ventana ya resuelta ni corre el
    deadline — el UPSERT solo completa el diagnóstico y solo si faltaba."""
    repo = SqlAlchemyRequestValidationRepository(db_session)
    await repo.start(_start(deadline_minutes=60))
    original = await db_session.get_one(RequestValidationModel, 974325)
    original_deadline = original.deadline_at
    assert await repo.resolve(974325, VALIDATION_CONFIRMED) is True

    await repo.start(_start(deadline_minutes=600, diagnosis_headline="Otro"))

    db_session.expire_all()  # start/resolve van por Core: refrescar el identity map
    row = await db_session.get_one(RequestValidationModel, 974325)
    assert row.status == VALIDATION_CONFIRMED
    assert row.deadline_at == original_deadline
    assert row.diagnosis_headline == "Posible falla de sensor"  # no se pisó


async def test_start_completa_el_diagnostico_de_una_fila_sin_chequear(
    db_session: AsyncSession,
) -> None:
    """Caso real PHC5R18423: la fila existía de una versión anterior sin diagnóstico
    (swap_checked=false) — el próximo start la completa sin reiniciar el reloj."""
    repo = SqlAlchemyRequestValidationRepository(db_session)
    old_deadline = datetime.now(UTC) + timedelta(minutes=30)
    db_session.add(
        RequestValidationModel(
            hp_request_id=974325,
            customer_id=8,
            device_id=7,
            device_serial="SERIE1",
            sku="CF230A",
            deadline_at=old_deadline,
            status="PENDING",
            swap_checked=False,
        )
    )
    await db_session.flush()

    await repo.start(_start(deadline_minutes=600, swap_note="Cambio de cartucho detectado"))

    db_session.expire_all()  # el UPSERT va por Core: refrescar el identity map
    row = await db_session.get_one(RequestValidationModel, 974325)
    assert row.swap_checked is True
    assert row.swap_note == "Cambio de cartucho detectado"
    assert row.diagnosis_headline == "Posible falla de sensor"
    assert row.deadline_at == old_deadline  # el reloj original no se reinicia


async def test_resolve_es_seguro_ante_carreras(db_session: AsyncSession) -> None:
    """La primera transición gana; la segunda no toca nada y devuelve False — es lo
    que evita duplicar AUTO_DISMISSED en el Historial."""
    repo = SqlAlchemyRequestValidationRepository(db_session)
    await repo.start(_start())

    assert await repo.resolve(974325, VALIDATION_DISMISSED) is True
    assert await repo.resolve(974325, VALIDATION_CONFIRMED) is False

    row = await db_session.get_one(RequestValidationModel, 974325)
    assert row.status == VALIDATION_DISMISSED
    assert row.resolved_at is not None


async def test_get_all_pending_calcula_is_due_en_sql(db_session: AsyncSession) -> None:
    repo = SqlAlchemyRequestValidationRepository(db_session)
    await repo.start(_start(hp_request_id=974325, deadline_minutes=0))  # ya vencida
    await repo.start(_start(hp_request_id=974326, deadline_minutes=360))
    await repo.start(_start(hp_request_id=974327, deadline_minutes=0))
    await repo.resolve(974327, VALIDATION_DISMISSED)  # resuelta: no aparece

    pending = {row.hp_request_id: row for row in await repo.get_all_pending()}

    assert set(pending) == {974325, 974326}
    assert pending[974325].is_due is True
    assert pending[974326].is_due is False
    assert pending[974325].sku == "CF230A"

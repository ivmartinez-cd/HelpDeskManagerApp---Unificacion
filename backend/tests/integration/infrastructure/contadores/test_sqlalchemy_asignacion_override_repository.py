"""Round-trip del repo de overrides de asignación (contadores) contra Postgres."""

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.contadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.contadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)


async def _creador(session: AsyncSession) -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name="Admin Prueba",
    )
    session.add(user)
    await session.flush()
    return user.id


def _override(
    *,
    creador: uuid.UUID,
    ausente: str = "vipaez",
    alcance: frozenset[str] | None = None,
) -> AsignacionOverride:
    return AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id="reemplazo",
        vigente_desde=date(2026, 8, 1),
        vigente_hasta=date(2026, 8, 31),
        alcance="TOTAL" if alcance is None else alcance,
        estado="ACTIVA",
        motivo="vacaciones",
        created_by_user_id=creador,
    )


async def test_override_total_round_trip_listados_y_cancelacion(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    creador = await _creador(db_session)
    override = _override(creador=creador)
    await repo.create(override)

    leido = await repo.get_by_id(override.id)
    assert leido is not None and leido.alcance == "TOTAL" and leido.estado == "ACTIVA"
    assert await repo.get_by_id(uuid.uuid4()) is None
    assert [o.id for o in await repo.list_all()] == [override.id]
    assert [o.id for o in await repo.list_activos()] == [override.id]
    assert [o.id for o in await repo.list_activos_por_ausente("vipaez")] == [override.id]
    assert await repo.list_activos_por_ausente("nadie") == []
    assert [o.id for o in await repo.list_activos_por_reemplazante("reemplazo")] == [override.id]

    await repo.cancelar(override.id)
    cancelado = await repo.get_by_id(override.id)
    assert cancelado is not None and cancelado.estado == "CANCELADA"
    assert await repo.list_activos() == []
    assert await repo.list_activos_por_reemplazante("reemplazo") == []
    await repo.cancelar(uuid.uuid4())  # id inexistente: no-op


async def test_override_parcial_persiste_los_clientes_del_alcance(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyAsignacionOverrideRepository(db_session)
    creador = await _creador(db_session)
    override = _override(creador=creador, alcance=frozenset({"YAGUAR", "EDERSA"}))
    await repo.create(override)

    leido = await repo.get_by_id(override.id)
    assert leido is not None and leido.alcance == frozenset({"YAGUAR", "EDERSA"})

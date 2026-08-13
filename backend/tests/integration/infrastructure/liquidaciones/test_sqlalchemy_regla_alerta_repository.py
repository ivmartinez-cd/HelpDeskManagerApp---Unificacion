"""Tests de integración de SqlAlchemyReglaAlertaRepository contra Postgres real.

Sin `create()` en el repo (solo lectura, la carga real es vía seed de Alembic) —
las filas de fixture se insertan directo con el modelo.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.liquidaciones.infrastructure.models.regla_alerta_model import ReglaAlertaModel
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_regla_alerta_repository import (  # noqa: E501
    SqlAlchemyReglaAlertaRepository,
)


async def _create_regla(
    db_session: AsyncSession, *, codigo: str, activa: bool = True
) -> ReglaAlertaModel:
    model = ReglaAlertaModel(
        id=uuid.uuid4(),
        codigo=codigo,
        nombre=f"Regla {codigo}",
        descripcion=None,
        activa=activa,
        riesgo_base=1.0,
        configuracion={},
    )
    db_session.add(model)
    await db_session.flush()
    return model


async def test_list_activas_excludes_inactive_rules(db_session: AsyncSession) -> None:
    await _create_regla(db_session, codigo="ALT001", activa=True)
    await _create_regla(db_session, codigo="ALT006", activa=False)

    activas = await SqlAlchemyReglaAlertaRepository(db_session).list_activas()

    assert "ALT001" in activas
    assert "ALT006" not in activas


async def test_list_activas_is_keyed_by_codigo(db_session: AsyncSession) -> None:
    await _create_regla(db_session, codigo="ALT002", activa=True)

    activas = await SqlAlchemyReglaAlertaRepository(db_session).list_activas()

    assert activas["ALT002"].codigo == "ALT002"


async def test_list_all_returns_ordered_by_codigo(db_session: AsyncSession) -> None:
    await _create_regla(db_session, codigo="ALT005", activa=True)
    await _create_regla(db_session, codigo="ALT001", activa=False)

    todas = await SqlAlchemyReglaAlertaRepository(db_session).list_all()

    assert [r.codigo for r in todas] == ["ALT001", "ALT005"]

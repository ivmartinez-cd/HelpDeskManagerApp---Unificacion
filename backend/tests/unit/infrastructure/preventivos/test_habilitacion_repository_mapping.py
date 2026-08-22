"""Parte pura del repositorio SQLAlchemy de habilitaciones (sin base de
datos): mapeo modelo -> entidad y el atajo de lista vacía que no toca la
sesión. Las consultas reales son tests de integración."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.preventivos.infrastructure.models.habilitacion_model import (
    HabilitacionPreventivoModel,
)
from src.modules.preventivos.infrastructure.repositories.sqlalchemy_habilitacion_repository import (
    SqlAlchemyHabilitacionRepository,
    _to_entity,
)


class _SesionQueNoDebeUsarse:
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("la sesión no tendría que usarse con lista vacía")


def test_to_entity_copia_todos_los_campos_del_modelo() -> None:
    id_ = uuid.uuid4()
    user_id = uuid.uuid4()
    habilitado_en = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)
    deshabilitado_en = datetime(2026, 8, 10, 9, 0, tzinfo=UTC)
    modelo = HabilitacionPreventivoModel(
        id=id_,
        siges_maquina_id=4321,
        habilitado_por_user_id=user_id,
        habilitado_por_nombre="Ana Prueba",
        habilitado_en=habilitado_en,
        nota="revisar rodillos",
        activa=False,
        deshabilitado_en=deshabilitado_en,
        deshabilitado_por="sistema",
    )

    entidad = _to_entity(modelo)

    assert entidad.id == id_
    assert entidad.siges_maquina_id == 4321
    assert entidad.habilitado_por_user_id == user_id
    assert entidad.habilitado_por_nombre == "Ana Prueba"
    assert entidad.habilitado_en == habilitado_en
    assert entidad.nota == "revisar rodillos"
    assert entidad.activa is False
    assert entidad.deshabilitado_en == deshabilitado_en
    assert entidad.deshabilitado_por == "sistema"


async def test_list_activas_por_maquinas_vacia_no_consulta() -> None:
    repo = SqlAlchemyHabilitacionRepository(cast(AsyncSession, _SesionQueNoDebeUsarse()))

    assert await repo.list_activas_por_maquinas([]) == []

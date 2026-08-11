import uuid

import pytest

from src.modules.turnos.application.dtos.turno_dtos import (
    CreateCasillaCommand,
    UpdateCasillaCommand,
)
from src.modules.turnos.application.use_cases.upsert_casilla import (
    UpsertCasilla,
    UpsertCasillaDependencies,
)
from tests.unit.domain.turnos.fakes import FakeCasillaRepository


async def test_update_preserva_color_orden_y_activo_al_renombrar() -> None:
    """La UI solo edita el nombre -- el PUT no debe resetear color/sort_order/
    is_active a los defaults de CasillaRequest (bug real: cualquier renombre
    volvía la casilla a color null, sort_order 0, is_active true)."""
    repo = FakeCasillaRepository()
    use_case = UpsertCasilla(UpsertCasillaDependencies(casillas=repo))
    original = await use_case.create(
        CreateCasillaCommand(nombre="INSUMOS", color="#8b5cf6", sort_order=3, is_active=False)
    )

    renamed = await use_case.update(
        UpdateCasillaCommand(casilla_id=original.id, nombre="INSUMOS RENOMBRADA")
    )

    assert renamed.nombre == "INSUMOS RENOMBRADA"
    assert renamed.color == "#8b5cf6"
    assert renamed.sort_order == 3
    assert renamed.is_active is False


async def test_update_casilla_inexistente_falla() -> None:
    repo = FakeCasillaRepository()
    use_case = UpsertCasilla(UpsertCasillaDependencies(casillas=repo))

    with pytest.raises(ValueError, match="no existe"):
        await use_case.update(UpdateCasillaCommand(casilla_id=uuid.uuid4(), nombre="X"))

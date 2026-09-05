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
from src.modules.turnos.domain.errors import (
    CasillaNombreDuplicadoError,
    CasillaNombreVacioError,
    CasillaNotFoundError,
)
from tests.unit.domain.turnos.fakes import FakeCasillaRepository


def _use_case() -> tuple[UpsertCasilla, FakeCasillaRepository]:
    repo = FakeCasillaRepository()
    return UpsertCasilla(UpsertCasillaDependencies(casillas=repo)), repo


async def test_update_preserva_color_orden_y_activo_al_renombrar() -> None:
    """La UI solo edita el nombre -- el PUT no debe resetear color/sort_order/
    is_active a los defaults de CasillaRequest (bug real: cualquier renombre
    volvía la casilla a color null, sort_order 0, is_active true)."""
    use_case, _ = _use_case()
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
    use_case, _ = _use_case()

    with pytest.raises(CasillaNotFoundError, match="no existe"):
        await use_case.update(UpdateCasillaCommand(casilla_id=uuid.uuid4(), nombre="X"))


async def test_nombre_vacio_o_solo_espacios_se_rechaza() -> None:
    use_case, repo = _use_case()

    with pytest.raises(CasillaNombreVacioError):
        await use_case.create(CreateCasillaCommand(nombre="   ", color=None))
    assert repo.rows == {}


async def test_nombre_se_guarda_sin_espacios_en_los_bordes() -> None:
    use_case, _ = _use_case()

    creada = await use_case.create(CreateCasillaCommand(nombre="  ST  ", color=None))

    assert creada.nombre == "ST"


async def test_nombre_duplicado_al_crear_es_conflicto_no_500() -> None:
    """Antes el unique de `turno_casilla.nombre` reventaba en el flush como
    IntegrityError -> 500; ahora es una regla de dominio (409)."""
    use_case, repo = _use_case()
    await use_case.create(CreateCasillaCommand(nombre="INSUMOS", color=None))

    with pytest.raises(CasillaNombreDuplicadoError, match="INSUMOS"):
        await use_case.create(CreateCasillaCommand(nombre="INSUMOS", color=None))
    assert len(repo.rows) == 1


async def test_renombrar_a_un_nombre_ajeno_es_conflicto() -> None:
    use_case, _ = _use_case()
    await use_case.create(CreateCasillaCommand(nombre="INSUMOS", color=None))
    st = await use_case.create(CreateCasillaCommand(nombre="ST", color=None))

    with pytest.raises(CasillaNombreDuplicadoError):
        await use_case.update(UpdateCasillaCommand(casilla_id=st.id, nombre="INSUMOS"))


async def test_renombrar_con_el_propio_nombre_no_conflictua() -> None:
    use_case, _ = _use_case()
    st = await use_case.create(CreateCasillaCommand(nombre="ST", color=None))

    renamed = await use_case.update(UpdateCasillaCommand(casilla_id=st.id, nombre="ST"))

    assert renamed.nombre == "ST"

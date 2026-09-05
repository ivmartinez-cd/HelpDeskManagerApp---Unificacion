import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.config_spsts import (
    ConfigSpstsPorts,
    CreateSpst,
    DeleteSpst,
    ToggleSpstActivo,
    UpdateSpst,
)
from src.modules.liquidaciones.domain.errors import SpstNoEncontradoError
from tests.unit.domain.liquidaciones.factories import make_spst
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigSpstRepository


def _ports(repo: FakeConfigSpstRepository) -> ConfigSpstsPorts:
    return ConfigSpstsPorts(spsts=repo)


async def test_create_persiste() -> None:
    repo = FakeConfigSpstRepository()
    prestador_id = uuid.uuid4()

    creado = await CreateSpst(_ports(repo)).execute(
        prestador_id=prestador_id,
        nombre="SPST Norte",
        domicilio=None,
        localidad="Salta",
        provincia="Salta",
        zona_cobertura="NOA",
    )

    assert creado.prestador_id == prestador_id
    assert [s.nombre for s in repo.rows] == ["SPST Norte"]


async def test_update_persiste() -> None:
    existente = make_spst(nombre="Viejo")
    repo = FakeConfigSpstRepository([existente])

    updated = await UpdateSpst(_ports(repo)).execute(
        existente.id,
        nombre="Nuevo",
        domicilio="Calle 1",
        localidad=None,
        provincia=None,
        zona_cobertura=None,
    )

    assert updated.nombre == "Nuevo"
    assert repo.rows[0].domicilio == "Calle 1"


async def test_update_inexistente_lanza_not_found() -> None:
    repo = FakeConfigSpstRepository()

    with pytest.raises(SpstNoEncontradoError):
        await UpdateSpst(_ports(repo)).execute(
            uuid.uuid4(),
            nombre="X",
            domicilio=None,
            localidad=None,
            provincia=None,
            zona_cobertura=None,
        )


async def test_toggle_activo() -> None:
    existente = make_spst(activo=True)
    repo = FakeConfigSpstRepository([existente])

    updated = await ToggleSpstActivo(_ports(repo)).execute(existente.id, activo=False)

    assert updated.activo is False


async def test_delete_elimina() -> None:
    existente = make_spst()
    repo = FakeConfigSpstRepository([existente])

    await DeleteSpst(_ports(repo)).execute(existente.id)

    assert repo.rows == []


async def test_delete_inexistente_lanza_not_found() -> None:
    repo = FakeConfigSpstRepository()

    with pytest.raises(SpstNoEncontradoError):
        await DeleteSpst(_ports(repo)).execute(uuid.uuid4())

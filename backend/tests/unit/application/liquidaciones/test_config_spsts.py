import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.config_spsts import (
    ConfigSpstsPorts,
    CreateSpst,
    DeleteSpst,
    ToggleSpstActivo,
    UpdateSpst,
)
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    SpstNoEncontradoError,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_spst
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigPrestadorRepository,
    FakeConfigSpstRepository,
)


def _ports(
    repo: FakeConfigSpstRepository,
    prestadores: FakeConfigPrestadorRepository | None = None,
) -> ConfigSpstsPorts:
    return ConfigSpstsPorts(spsts=repo, prestadores=prestadores)


async def test_create_con_prestador_inexistente_lanza_not_found() -> None:
    repo = FakeConfigSpstRepository()
    prestadores = FakeConfigPrestadorRepository()

    with pytest.raises(PrestadorNoEncontradoError):
        await CreateSpst(_ports(repo, prestadores)).execute(
            prestador_id=uuid.uuid4(),
            nombre="Huérfano",
            domicilio=None,
            localidad=None,
            provincia=None,
            zona_cobertura=None,
        )

    assert repo.rows == []


async def test_create_con_prestador_existente_persiste() -> None:
    prestador = make_prestador()
    repo = FakeConfigSpstRepository()
    prestadores = FakeConfigPrestadorRepository({prestador.id: prestador})

    creado = await CreateSpst(_ports(repo, prestadores)).execute(
        prestador_id=prestador.id,
        nombre="SPST Sur",
        domicilio=None,
        localidad=None,
        provincia=None,
        zona_cobertura=None,
    )

    assert creado.prestador_id == prestador.id
    assert len(repo.rows) == 1


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

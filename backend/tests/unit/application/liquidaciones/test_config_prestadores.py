import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.config_prestadores import (
    ConfigPrestadoresPorts,
    CreatePrestador,
    DeletePrestador,
    TogglePrestadorActivo,
    UpdatePrestador,
)
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigPrestadorRepository


def _ports(repo: FakeConfigPrestadorRepository) -> ConfigPrestadoresPorts:
    return ConfigPrestadoresPorts(prestadores=repo)


async def test_create_normaliza_nombre_corto() -> None:
    repo = FakeConfigPrestadorRepository()

    creado = await CreatePrestador(_ports(repo)).execute(
        nombre="Pentacom SA", nombre_corto="  pentacom ", cuit=None, region=None
    )

    assert creado.nombre_corto == "PENTACOM"
    assert repo.rows[creado.id].nombre_corto == "PENTACOM"


async def test_update_normaliza_y_persiste() -> None:
    existente = make_prestador(nombre_corto="VIEJO")
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    updated = await UpdatePrestador(_ports(repo)).execute(
        existente.id, nombre="Nuevo Nombre", nombre_corto="nuevo", cuit="30-1", region="Sur"
    )

    assert updated.nombre_corto == "NUEVO"
    assert repo.rows[existente.id].nombre == "Nuevo Nombre"


async def test_update_inexistente_lanza_not_found() -> None:
    repo = FakeConfigPrestadorRepository()

    with pytest.raises(PrestadorNoEncontradoError):
        await UpdatePrestador(_ports(repo)).execute(
            uuid.uuid4(), nombre="X", nombre_corto="X", cuit=None, region=None
        )


async def test_toggle_activo() -> None:
    existente = make_prestador(activo=True)
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    updated = await TogglePrestadorActivo(_ports(repo)).execute(existente.id, activo=False)

    assert updated.activo is False


async def test_toggle_inexistente_lanza_not_found() -> None:
    repo = FakeConfigPrestadorRepository()

    with pytest.raises(PrestadorNoEncontradoError):
        await TogglePrestadorActivo(_ports(repo)).execute(uuid.uuid4(), activo=False)


async def test_delete_elimina() -> None:
    existente = make_prestador()
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    await DeletePrestador(_ports(repo)).execute(existente.id)

    assert existente.id not in repo.rows


async def test_delete_inexistente_lanza_not_found() -> None:
    repo = FakeConfigPrestadorRepository()

    with pytest.raises(PrestadorNoEncontradoError):
        await DeletePrestador(_ports(repo)).execute(uuid.uuid4())

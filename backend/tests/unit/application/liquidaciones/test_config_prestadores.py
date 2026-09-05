import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.config_prestadores import (
    ConfigPrestadoresPorts,
    CreatePrestador,
    DeletePrestador,
    TogglePrestadorActivo,
    UpdatePrestador,
)
from src.modules.liquidaciones.domain.errors import (
    PrestadorDuplicadoError,
    PrestadorNoEncontradoError,
)
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


async def test_create_con_nombre_corto_duplicado_lanza_conflicto() -> None:
    existente = make_prestador(nombre_corto="PENTACOM")
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    # El chequeo compara ya normalizado: " pentacom " choca con "PENTACOM".
    with pytest.raises(PrestadorDuplicadoError):
        await CreatePrestador(_ports(repo)).execute(
            nombre="Otro", nombre_corto=" pentacom ", cuit=None, region=None
        )

    assert len(repo.rows) == 1


async def test_update_normaliza_y_persiste() -> None:
    existente = make_prestador(nombre_corto="VIEJO")
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    updated = await UpdatePrestador(_ports(repo)).execute(
        existente.id, nombre="Nuevo Nombre", nombre_corto="nuevo", cuit="30-1", region="Sur"
    )

    assert updated.nombre_corto == "NUEVO"
    assert repo.rows[existente.id].nombre == "Nuevo Nombre"


async def test_update_conservando_su_propio_nombre_corto_no_es_duplicado() -> None:
    existente = make_prestador(nombre_corto="PENTACOM")
    repo = FakeConfigPrestadorRepository({existente.id: existente})

    updated = await UpdatePrestador(_ports(repo)).execute(
        existente.id, nombre="Pentacom SA", nombre_corto="pentacom", cuit=None, region=None
    )

    assert updated.nombre_corto == "PENTACOM"


async def test_update_al_nombre_corto_de_otro_lanza_conflicto() -> None:
    uno = make_prestador(nombre_corto="UNO")
    otro = make_prestador(nombre_corto="OTRO")
    repo = FakeConfigPrestadorRepository({uno.id: uno, otro.id: otro})

    with pytest.raises(PrestadorDuplicadoError):
        await UpdatePrestador(_ports(repo)).execute(
            uno.id, nombre=uno.nombre, nombre_corto="otro", cuit=None, region=None
        )

    assert repo.rows[uno.id].nombre_corto == "UNO"


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

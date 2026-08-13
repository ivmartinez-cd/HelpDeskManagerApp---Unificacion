import dataclasses
import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.config_tabla_km import (
    ConfigTablaKmPorts,
    CreateTablaKm,
    DeleteTablaKm,
    TablaKmDatos,
    UpdateTablaKm,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import TablaKmNoEncontradaError
from tests.unit.domain.liquidaciones.factories import make_tabla_km
from tests.unit.domain.liquidaciones.fakes_config import FakeConfigTablaKmRepository


def _ports(repo: FakeConfigTablaKmRepository) -> ConfigTablaKmPorts:
    return ConfigTablaKmPorts(tabla_km=repo)


def _datos_de(fila: TablaKm, **overrides: object) -> TablaKmDatos:
    campos = {f.name: getattr(fila, f.name) for f in dataclasses.fields(TablaKmDatos)}
    campos.update(overrides)
    return TablaKmDatos(**campos)  # type: ignore[arg-type]


async def test_create_persiste() -> None:
    repo = FakeConfigTablaKmRepository()
    fila = make_tabla_km(empresa_nombre="Banco Río", sucursal_nombre="Centro")

    creada = await CreateTablaKm(_ports(repo)).execute(_datos_de(fila))

    assert creada.empresa_nombre == "Banco Río"
    assert [t.sucursal_nombre for t in repo.rows] == ["Centro"]


async def test_update_persiste() -> None:
    existente = make_tabla_km(kms_recorrido=100.0)
    repo = FakeConfigTablaKmRepository([existente])

    updated = await UpdateTablaKm(_ports(repo)).execute(
        existente.id, _datos_de(existente, kms_recorrido=250.0)
    )

    assert updated.kms_recorrido == 250.0
    assert repo.rows[0].kms_recorrido == 250.0


async def test_update_inexistente_lanza_not_found() -> None:
    repo = FakeConfigTablaKmRepository()

    with pytest.raises(TablaKmNoEncontradaError):
        await UpdateTablaKm(_ports(repo)).execute(uuid.uuid4(), _datos_de(make_tabla_km()))


async def test_delete_elimina() -> None:
    existente = make_tabla_km()
    repo = FakeConfigTablaKmRepository([existente])

    await DeleteTablaKm(_ports(repo)).execute(existente.id)

    assert repo.rows == []


async def test_delete_inexistente_lanza_not_found() -> None:
    repo = FakeConfigTablaKmRepository()

    with pytest.raises(TablaKmNoEncontradaError):
        await DeleteTablaKm(_ports(repo)).execute(uuid.uuid4())

import uuid

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import CreatePrestadorCommand
from src.modules.prestadores.application.use_cases.create_prestador import (
    CreatePrestador,
    CreatePrestadorDependencies,
)
from src.modules.prestadores.domain.errors import (
    OperadorNoEncontradoError,
    PrestadorDuplicadoError,
)
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionHistorialRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)


def _deps(
    prestadores: FakePrestadorRepository,
    asignaciones: FakeAsignacionHistorialRepository,
    users: FakeUserProvider,
) -> CreatePrestadorDependencies:
    return CreatePrestadorDependencies(
        prestadores=prestadores, asignaciones=asignaciones, users=users
    )


def _command(**overrides: object) -> CreatePrestadorCommand:
    base = {
        "siges_empresa_id": 42,
        "den_comercial": "PST Córdoba",
        "razon_social": "PST Córdoba SRL",
        "cuit": "30-11111111-9",
        "operador_id": None,
    }
    base.update(overrides)
    return CreatePrestadorCommand(**base)  # type: ignore[arg-type]


async def test_alta_con_operador_abre_el_primer_tramo_de_historial() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    users = FakeUserProvider()
    operador_id = uuid.uuid4()
    users.users[operador_id] = UserInfo(id=operador_id, full_name="Ana Pérez")

    dto = await CreatePrestador(_deps(prestadores, asignaciones, users)).execute(
        _command(operador_id=operador_id)
    )

    assert dto.den_comercial == "PST Córdoba"
    assert dto.operador_nombre == "Ana Pérez"
    assert dto.is_active is True
    assert dto.id in prestadores.rows
    tramos = await asignaciones.list_by_prestador(dto.id)
    assert len(tramos) == 1
    assert tramos[0].operador_id == operador_id
    assert tramos[0].hasta is None


async def test_alta_sin_operador_no_abre_historial() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()

    dto = await CreatePrestador(_deps(prestadores, asignaciones, FakeUserProvider())).execute(
        _command(siges_empresa_id=7, den_comercial="PST Salta", razon_social=None, cuit=None)
    )

    assert dto.operador_id is None
    assert dto.operador_nombre is None
    assert await asignaciones.list_by_prestador(dto.id) == []


async def test_rechaza_siges_empresa_id_ya_vinculado() -> None:
    prestadores = FakePrestadorRepository()
    deps = _deps(prestadores, FakeAsignacionHistorialRepository(), FakeUserProvider())
    await CreatePrestador(deps).execute(_command(siges_empresa_id=99))

    with pytest.raises(PrestadorDuplicadoError):
        await CreatePrestador(deps).execute(
            _command(siges_empresa_id=99, den_comercial="Otro nombre")
        )

    assert len(prestadores.rows) == 1


async def test_rechaza_operador_inexistente_sin_persistir() -> None:
    prestadores = FakePrestadorRepository()
    asignaciones = FakeAsignacionHistorialRepository()
    deps = _deps(prestadores, asignaciones, FakeUserProvider())

    with pytest.raises(OperadorNoEncontradoError):
        await CreatePrestador(deps).execute(_command(operador_id=uuid.uuid4()))

    assert prestadores.rows == {}
    assert asignaciones.rows == {}

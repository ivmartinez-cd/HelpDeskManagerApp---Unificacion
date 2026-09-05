import uuid
from datetime import date

import pytest

from src.modules.prestadores.application.dtos.prestador_dtos import (
    CreateAsignacionOverrideCommand,
)
from src.modules.prestadores.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.domain.errors import (
    InvalidOverrideRangeError,
    OperadorNoEncontradoError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
    PrestadorNotFoundError,
)
from src.modules.prestadores.domain.repositories.user_provider import UserInfo
from tests.unit.domain.prestadores.fakes import (
    FakeAsignacionOverrideRepository,
    FakePrestadorRepository,
    FakeUserProvider,
)

_AUSENTE = uuid.uuid4()
_REEMPLAZANTE = uuid.uuid4()


def _command(**overrides: object) -> CreateAsignacionOverrideCommand:
    base = {
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 15),
        "prestador_ids": None,
        "motivo": "vacaciones",
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return CreateAsignacionOverrideCommand(**base)  # type: ignore[arg-type]


_PRESTADORES = FakePrestadorRepository()


def _pst_existente() -> uuid.UUID:
    pst = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=len(_PRESTADORES.rows) + 1,
        den_comercial="PST",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=_AUSENTE,
        is_active=True,
    )
    _PRESTADORES.rows[pst.id] = pst
    return pst.id


def _deps(overrides: FakeAsignacionOverrideRepository) -> CreateAsignacionOverrideDependencies:
    users = FakeUserProvider()
    users.users[_AUSENTE] = UserInfo(id=_AUSENTE, full_name="Ausente Real")
    users.users[_REEMPLAZANTE] = UserInfo(id=_REEMPLAZANTE, full_name="Reemplazante Real")
    return CreateAsignacionOverrideDependencies(
        overrides=overrides, users=users, prestadores=_PRESTADORES
    )


async def test_crea_override_alcance_total() -> None:
    repo = FakeAsignacionOverrideRepository()

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command())

    assert dto.alcance_total is True
    assert dto.prestador_ids == []
    assert dto.operador_ausente_nombre == "Ausente Real"
    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 1


async def test_crea_override_alcance_por_prestador() -> None:
    repo = FakeAsignacionOverrideRepository()
    pst = _pst_existente()

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command(prestador_ids=[pst]))

    assert dto.alcance_total is False
    assert dto.prestador_ids == [pst]


async def test_rechaza_operadores_inexistentes_sin_persistir() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(OperadorNoEncontradoError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(operador_ausente_id=uuid.uuid4())
        )
    with pytest.raises(OperadorNoEncontradoError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(operador_reemplazante_id=uuid.uuid4())
        )
    assert repo.rows == {}


async def test_rechaza_prestador_inexistente_en_el_alcance() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(PrestadorNotFoundError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(prestador_ids=[_pst_existente(), uuid.uuid4()])
        )
    assert repo.rows == {}


async def test_rechaza_rango_invalido() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(InvalidOverrideRangeError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(desde=date(2026, 8, 15), hasta=date(2026, 8, 1))
        )


async def test_rechaza_mismo_operador_como_ausente_y_reemplazante() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(OverrideMismoOperadorError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(operador_reemplazante_id=_AUSENTE)
        )


async def test_rechaza_solapamiento_con_override_total_existente() -> None:
    repo = FakeAsignacionOverrideRepository()
    await CreateAsignacionOverride(_deps(repo)).execute(_command())

    with pytest.raises(OverlappingOverrideError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(desde=date(2026, 8, 10), hasta=date(2026, 8, 20))
        )


async def test_permite_overrides_del_mismo_ausente_sin_solapar_fechas() -> None:
    repo = FakeAsignacionOverrideRepository()
    await CreateAsignacionOverride(_deps(repo)).execute(_command())

    dto = await CreateAsignacionOverride(_deps(repo)).execute(
        _command(desde=date(2026, 9, 1), hasta=date(2026, 9, 10))
    )

    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 2


async def test_permite_overrides_puntuales_de_pst_distintos_con_fechas_solapadas() -> None:
    repo = FakeAsignacionOverrideRepository()
    pst_a, pst_b = _pst_existente(), _pst_existente()
    await CreateAsignacionOverride(_deps(repo)).execute(_command(prestador_ids=[pst_a]))

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command(prestador_ids=[pst_b]))

    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 2

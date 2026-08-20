import uuid
from datetime import date

import pytest

from src.modules.turnos.application.dtos.turno_dtos import CreateAsignacionOverrideCommand
from src.modules.turnos.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.turnos.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository, FakeUserProvider

_AUSENTE = uuid.uuid4()
_REEMPLAZANTE = uuid.uuid4()


def _command(**overrides: object) -> CreateAsignacionOverrideCommand:
    base = {
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 15),
        "slot_ids": None,
        "motivo": "vacaciones",
        "created_by_user_id": uuid.uuid4(),
    }
    base.update(overrides)
    return CreateAsignacionOverrideCommand(**base)  # type: ignore[arg-type]


def _deps(overrides: FakeAsignacionOverrideRepository) -> CreateAsignacionOverrideDependencies:
    users = FakeUserProvider()
    users.users[_AUSENTE] = UserInfo(id=_AUSENTE, full_name="Ausente Real")
    users.users[_REEMPLAZANTE] = UserInfo(id=_REEMPLAZANTE, full_name="Reemplazante Real")
    return CreateAsignacionOverrideDependencies(overrides=overrides, users=users)


async def test_crea_cobertura_alcance_total() -> None:
    repo = FakeAsignacionOverrideRepository()

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command())

    assert dto.alcance_total is True
    assert dto.slot_ids == []
    assert dto.operador_ausente_nombre == "Ausente Real"
    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 1


async def test_crea_cobertura_alcance_por_franja() -> None:
    repo = FakeAsignacionOverrideRepository()
    slot = uuid.uuid4()

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command(slot_ids=[slot]))

    assert dto.alcance_total is False
    assert dto.slot_ids == [slot]


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


async def test_rechaza_solapamiento_con_cobertura_total_existente() -> None:
    repo = FakeAsignacionOverrideRepository()
    await CreateAsignacionOverride(_deps(repo)).execute(_command())

    with pytest.raises(OverlappingOverrideError):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(desde=date(2026, 8, 10), hasta=date(2026, 8, 20))
        )


async def test_permite_coberturas_del_mismo_ausente_sin_solapar_fechas() -> None:
    repo = FakeAsignacionOverrideRepository()
    await CreateAsignacionOverride(_deps(repo)).execute(_command())

    dto = await CreateAsignacionOverride(_deps(repo)).execute(
        _command(desde=date(2026, 9, 1), hasta=date(2026, 9, 10))
    )

    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 2


async def test_permite_coberturas_puntuales_de_franjas_distintas_con_fechas_solapadas() -> None:
    repo = FakeAsignacionOverrideRepository()
    slot_a, slot_b = uuid.uuid4(), uuid.uuid4()
    await CreateAsignacionOverride(_deps(repo)).execute(_command(slot_ids=[slot_a]))

    dto = await CreateAsignacionOverride(_deps(repo)).execute(_command(slot_ids=[slot_b]))

    assert dto.estado == "ACTIVA"
    assert len(repo.rows) == 2

"""Intercambio de turnos (ADR-026): alta del par de coberturas cruzadas."""

import uuid
from datetime import date

import pytest

from src.modules.turnos.application.dtos.turno_dtos import (
    CreateAsignacionOverrideCommand,
    IntercambioCommand,
)
from src.modules.turnos.application.use_cases.create_asignacion_override import (
    CreateAsignacionOverride,
    CreateAsignacionOverrideDependencies,
)
from src.modules.turnos.application.use_cases.create_intercambio import CreateIntercambio
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
)
from src.modules.turnos.domain.errors import (
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository, FakeUserProvider

_MAJO = uuid.uuid4()
_LUNA = uuid.uuid4()
_CREADOR = uuid.uuid4()


def _command(**overrides: object) -> IntercambioCommand:
    base = {
        "operador_a_id": _MAJO,
        "operador_b_id": _LUNA,
        "desde": date(2026, 8, 20),
        "hasta": date(2026, 8, 20),
        "slot_ids_a": None,
        "slot_ids_b": None,
        "motivo": None,
        "created_by_user_id": _CREADOR,
    }
    base.update(overrides)
    return IntercambioCommand(**base)  # type: ignore[arg-type]


def _deps(repo: FakeAsignacionOverrideRepository) -> IntercambioDependencies:
    users = FakeUserProvider()
    users.users[_MAJO] = UserInfo(id=_MAJO, full_name="Maria Jose Vela")
    users.users[_LUNA] = UserInfo(id=_LUNA, full_name="Luna")
    return IntercambioDependencies(overrides=repo, users=users)


async def test_crea_dos_coberturas_cruzadas_con_el_mismo_intercambio_id() -> None:
    repo = FakeAsignacionOverrideRepository()

    dto = await CreateIntercambio(_deps(repo)).execute(_command())

    assert len(dto.coberturas) == 2
    ida, vuelta = dto.coberturas
    assert (ida.operador_ausente_id, ida.operador_reemplazante_id) == (_MAJO, _LUNA)
    assert (vuelta.operador_ausente_id, vuelta.operador_reemplazante_id) == (_LUNA, _MAJO)
    assert ida.operador_ausente_nombre == "Maria Jose Vela"
    assert {c.intercambio_id for c in dto.coberturas} == {dto.intercambio_id}
    assert all(c.estado == "ACTIVA" and c.alcance_total for c in dto.coberturas)
    assert len(repo.rows) == 2


async def test_motivo_vacio_queda_como_intercambio() -> None:
    repo = FakeAsignacionOverrideRepository()

    dto = await CreateIntercambio(_deps(repo)).execute(_command(motivo="  "))

    assert all(c.motivo == "Intercambio" for c in dto.coberturas)


async def test_alcance_parcial_por_lado() -> None:
    repo = FakeAsignacionOverrideRepository()
    franja_majo, franja_luna = uuid.uuid4(), uuid.uuid4()

    dto = await CreateIntercambio(_deps(repo)).execute(
        _command(slot_ids_a=[franja_majo], slot_ids_b=[franja_luna])
    )

    ida, vuelta = dto.coberturas
    assert ida.slot_ids == [franja_majo]  # franja de Majo que toma Luna
    assert vuelta.slot_ids == [franja_luna]  # franja de Luna que toma Majo


async def test_rechaza_rango_invalido() -> None:
    with pytest.raises(InvalidOverrideRangeError):
        await CreateIntercambio(_deps(FakeAsignacionOverrideRepository())).execute(
            _command(desde=date(2026, 8, 21), hasta=date(2026, 8, 20))
        )


async def test_rechaza_mismo_operador_en_ambos_lados() -> None:
    with pytest.raises(OverrideMismoOperadorError):
        await CreateIntercambio(_deps(FakeAsignacionOverrideRepository())).execute(
            _command(operador_b_id=_MAJO)
        )


async def test_rechaza_si_un_lado_pisa_una_cobertura_activa_de_ese_ausente() -> None:
    repo = FakeAsignacionOverrideRepository()
    # Luna ya está cubierta por otro ese día (cobertura común, alcance total).
    otro = uuid.uuid4()
    users = FakeUserProvider()
    users.users[_LUNA] = UserInfo(id=_LUNA, full_name="Luna")
    users.users[otro] = UserInfo(id=otro, full_name="Otro Operador")
    deps_comun = CreateAsignacionOverrideDependencies(overrides=repo, users=users)
    await CreateAsignacionOverride(deps_comun).execute(
        CreateAsignacionOverrideCommand(
            operador_ausente_id=_LUNA,
            operador_reemplazante_id=otro,
            desde=date(2026, 8, 20),
            hasta=date(2026, 8, 20),
            slot_ids=None,
            motivo=None,
            created_by_user_id=_CREADOR,
        )
    )

    with pytest.raises(OverlappingOverrideError):
        await CreateIntercambio(_deps(repo)).execute(_command())
    # Atómico: no quedó ni la mitad de Majo.
    assert len(repo.rows) == 1


async def test_dos_intercambios_del_mismo_par_en_fechas_distintas_conviven() -> None:
    repo = FakeAsignacionOverrideRepository()
    await CreateIntercambio(_deps(repo)).execute(_command())

    dto = await CreateIntercambio(_deps(repo)).execute(
        _command(desde=date(2026, 8, 27), hasta=date(2026, 8, 27))
    )

    assert len(repo.rows) == 4
    assert len({o.intercambio_id for o in repo.rows.values()}) == 2
    assert dto.intercambio_id is not None

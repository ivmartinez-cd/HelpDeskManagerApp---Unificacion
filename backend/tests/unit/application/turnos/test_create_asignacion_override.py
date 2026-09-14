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
    ReemplazanteConTurnoSolapadoError,
    UsuarioNotFoundError,
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


async def test_operador_inexistente_es_not_found_no_500() -> None:
    """La FK a `app_user` fallaba en el flush como IntegrityError -> 500."""
    repo = FakeAsignacionOverrideRepository()
    fantasma = uuid.uuid4()

    with pytest.raises(UsuarioNotFoundError, match=str(fantasma)):
        await CreateAsignacionOverride(_deps(repo)).execute(
            _command(operador_reemplazante_id=fantasma)
        )
    assert repo.rows == {}



async def test_rechaza_reemplazante_con_turno_solapado_en_otra_casilla() -> None:
    from datetime import time

    from src.modules.turnos.domain.entities.asignacion import Asignacion
    from src.modules.turnos.domain.entities.slot import Slot
    from tests.unit.domain.turnos.fakes import FakeAsignacionRepository, FakeSlotRepository

    repo = FakeAsignacionOverrideRepository()
    slots_repo = FakeSlotRepository()
    asigs_repo = FakeAsignacionRepository()

    casilla_insumos = uuid.uuid4()
    casilla_st = uuid.uuid4()

    # Slot de Victor en ST: 9 a 13 (Lunes, dia 0)
    slot_victor = Slot(
        id=uuid.uuid4(), casilla_id=casilla_st, hora_inicio=time(9), hora_fin=time(13),
        dia_semana=0, sort_order=0,
    )
    # Slot de Luna en Insumos: 11 a 13 (Lunes, dia 0)
    slot_luna = Slot(
        id=uuid.uuid4(), casilla_id=casilla_insumos, hora_inicio=time(11), hora_fin=time(13),
        dia_semana=0, sort_order=0,
    )

    asig_victor = Asignacion(
        id=uuid.uuid4(), slot_id=slot_victor.id, user_id=_AUSENTE,
        vigente_desde=date(2026, 1, 1), vigente_hasta=None,
    )
    asig_luna = Asignacion(
        id=uuid.uuid4(), slot_id=slot_luna.id, user_id=_REEMPLAZANTE,
        vigente_desde=date(2026, 1, 1), vigente_hasta=None,
    )
    slots_repo.rows = {slot_victor.id: slot_victor, slot_luna.id: slot_luna}
    asigs_repo.rows = {asig_victor.id: asig_victor, asig_luna.id: asig_luna}

    deps = CreateAsignacionOverrideDependencies(
        overrides=repo,
        users=_deps(repo).users,
        slots=slots_repo,
        asignaciones=asigs_repo,
    )

    with pytest.raises(ReemplazanteConTurnoSolapadoError):
        await CreateAsignacionOverride(deps).execute(
            _command(slot_ids=[slot_victor.id], desde=date(2026, 9, 14), hasta=date(2026, 9, 14))
        )

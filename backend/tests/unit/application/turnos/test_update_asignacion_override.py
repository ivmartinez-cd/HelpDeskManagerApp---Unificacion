import uuid
from datetime import date

import pytest

from src.modules.turnos.application.dtos.turno_dtos import UpdateAsignacionOverrideCommand
from src.modules.turnos.application.use_cases.update_asignacion_override import (
    UpdateAsignacionOverride,
    UpdateAsignacionOverrideDependencies,
)
from src.modules.turnos.domain.errors import (
    AsignacionOverrideNotFoundError,
    InvalidOverrideRangeError,
    OverlappingOverrideError,
    OverrideMismoOperadorError,
    OverrideNoEditableError,
)
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository, FakeUserProvider

_AUSENTE = uuid.uuid4()
_REEMPLAZANTE = uuid.uuid4()
_OTRO_REEMPLAZANTE = uuid.uuid4()
_CREADOR = uuid.uuid4()


def _existente(**overrides: object) -> AsignacionOverride[uuid.UUID, uuid.UUID]:
    base = {
        "id": uuid.uuid4(),
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 15),
        "alcance": "TOTAL",
        "estado": "ACTIVA",
        "motivo": "vacaciones",
        "created_by_user_id": _CREADOR,
    }
    base.update(overrides)
    return AsignacionOverride(**base)  # type: ignore[arg-type]


def _command(override_id: uuid.UUID, **overrides: object) -> UpdateAsignacionOverrideCommand:
    base = {
        "override_id": override_id,
        "operador_ausente_id": _AUSENTE,
        "operador_reemplazante_id": _OTRO_REEMPLAZANTE,
        "desde": date(2026, 8, 1),
        "hasta": date(2026, 8, 20),
        "slot_ids": None,
        "motivo": "licencia",
    }
    base.update(overrides)
    return UpdateAsignacionOverrideCommand(**base)  # type: ignore[arg-type]


def _deps(overrides: FakeAsignacionOverrideRepository) -> UpdateAsignacionOverrideDependencies:
    users = FakeUserProvider()
    users.users[_AUSENTE] = UserInfo(id=_AUSENTE, full_name="Ausente Real")
    users.users[_OTRO_REEMPLAZANTE] = UserInfo(
        id=_OTRO_REEMPLAZANTE, full_name="Reemplazante Nuevo"
    )
    return UpdateAsignacionOverrideDependencies(overrides=overrides, users=users)


async def test_edita_campos_conservando_id_y_creador() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    dto = await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))

    assert dto.id == override.id
    assert dto.operador_reemplazante_nombre == "Reemplazante Nuevo"
    assert dto.hasta == date(2026, 8, 20)
    assert dto.motivo == "licencia"
    assert repo.rows[override.id].created_by_user_id == _CREADOR
    assert repo.rows[override.id].estado == "ACTIVA"


async def test_edita_alcance_de_total_a_parcial() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override
    slot = uuid.uuid4()

    dto = await UpdateAsignacionOverride(_deps(repo)).execute(
        _command(override.id, slot_ids=[slot])
    )

    assert dto.alcance_total is False
    assert dto.slot_ids == [slot]


async def test_editar_inexistente_lanza_not_found() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(AsignacionOverrideNotFoundError):
        await UpdateAsignacionOverride(_deps(repo)).execute(_command(uuid.uuid4()))


async def test_rechaza_editar_una_cobertura_cancelada() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente(estado="CANCELADA")
    repo.rows[override.id] = override

    with pytest.raises(OverrideNoEditableError):
        await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))


async def test_rechaza_rango_invalido() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    with pytest.raises(InvalidOverrideRangeError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, desde=date(2026, 8, 20), hasta=date(2026, 8, 1))
        )


async def test_rechaza_mismo_operador_como_ausente_y_reemplazante() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    with pytest.raises(OverrideMismoOperadorError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, operador_reemplazante_id=_AUSENTE)
        )


async def test_no_conflictua_consigo_misma_al_conservar_las_fechas() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    repo.rows[override.id] = override

    dto = await UpdateAsignacionOverride(_deps(repo)).execute(_command(override.id))

    assert dto.estado == "ACTIVA"


async def test_rechaza_solapamiento_con_otra_cobertura_del_mismo_ausente() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = _existente()
    otro = _existente(id=uuid.uuid4(), desde=date(2026, 9, 1), hasta=date(2026, 9, 10))
    repo.rows[override.id] = override
    repo.rows[otro.id] = otro

    with pytest.raises(OverlappingOverrideError):
        await UpdateAsignacionOverride(_deps(repo)).execute(
            _command(override.id, hasta=date(2026, 9, 5))
        )

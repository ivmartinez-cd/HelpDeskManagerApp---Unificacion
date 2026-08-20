"""Intercambio de turnos (ADR-026): cancelar siempre las dos mitades."""

import uuid
from datetime import date

import pytest

from src.modules.turnos.application.dtos.turno_dtos import IntercambioCommand
from src.modules.turnos.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.turnos.application.use_cases.cancel_intercambio import (
    CancelIntercambio,
    CancelIntercambioDependencies,
)
from src.modules.turnos.application.use_cases.create_intercambio import CreateIntercambio
from src.modules.turnos.application.use_cases.intercambio_support import (
    IntercambioDependencies,
)
from src.modules.turnos.domain.errors import IntercambioNotFoundError
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository, FakeUserProvider


async def _intercambio(repo: FakeAsignacionOverrideRepository) -> uuid.UUID:
    dto = await CreateIntercambio(
        IntercambioDependencies(overrides=repo, users=FakeUserProvider())
    ).execute(
        IntercambioCommand(
            operador_a_id=uuid.uuid4(),
            operador_b_id=uuid.uuid4(),
            desde=date(2026, 8, 20),
            hasta=date(2026, 8, 20),
            slot_ids_a=None,
            slot_ids_b=None,
            motivo=None,
            created_by_user_id=uuid.uuid4(),
        )
    )
    return dto.intercambio_id


async def test_cancela_las_dos_mitades() -> None:
    repo = FakeAsignacionOverrideRepository()
    intercambio_id = await _intercambio(repo)

    await CancelIntercambio(CancelIntercambioDependencies(overrides=repo)).execute(
        intercambio_id
    )

    assert [o.estado for o in repo.rows.values()] == ["CANCELADA", "CANCELADA"]


async def test_cancelar_inexistente_lanza_not_found() -> None:
    with pytest.raises(IntercambioNotFoundError):
        await CancelIntercambio(
            CancelIntercambioDependencies(overrides=FakeAsignacionOverrideRepository())
        ).execute(uuid.uuid4())


async def test_cancelar_una_mitad_como_cobertura_comun_cancela_el_par() -> None:
    repo = FakeAsignacionOverrideRepository()
    await _intercambio(repo)
    mitad = next(iter(repo.rows.values()))

    await CancelAsignacionOverride(CancelAsignacionOverrideDependencies(overrides=repo)).execute(
        mitad.id
    )

    assert [o.estado for o in repo.rows.values()] == ["CANCELADA", "CANCELADA"]

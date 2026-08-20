import uuid
from datetime import date

import pytest

from src.modules.turnos.application.use_cases.cancel_asignacion_override import (
    CancelAsignacionOverride,
    CancelAsignacionOverrideDependencies,
)
from src.modules.turnos.domain.errors import AsignacionOverrideNotFoundError
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride
from tests.unit.domain.turnos.fakes import FakeAsignacionOverrideRepository


async def test_cancela_una_cobertura_existente() -> None:
    repo = FakeAsignacionOverrideRepository()
    override = AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=uuid.uuid4(),
        operador_reemplazante_id=uuid.uuid4(),
        desde=date(2026, 8, 1),
        hasta=date(2026, 8, 15),
        alcance="TOTAL",
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )
    repo.rows[override.id] = override

    await CancelAsignacionOverride(CancelAsignacionOverrideDependencies(overrides=repo)).execute(
        override.id
    )

    assert repo.rows[override.id].estado == "CANCELADA"


async def test_cancelar_inexistente_lanza_not_found() -> None:
    repo = FakeAsignacionOverrideRepository()

    with pytest.raises(AsignacionOverrideNotFoundError):
        await CancelAsignacionOverride(
            CancelAsignacionOverrideDependencies(overrides=repo)
        ).execute(uuid.uuid4())

import uuid
from datetime import time

from src.modules.turnos.application.dtos.turno_dtos import CreateSlotCommand, UpdateSlotCommand
from src.modules.turnos.application.use_cases.upsert_slot import (
    UpsertSlot,
    UpsertSlotDependencies,
)
from tests.unit.domain.turnos.fakes import FakeSlotRepository


async def test_update_preserva_sort_order_al_editar_horario() -> None:
    """La UI solo edita hora_inicio/hora_fin/dia_semana -- el PUT no debe resetear
    sort_order a 0 (bug real: la tercera franja del día perdía su posición de
    despliegue apenas se le tocaba el horario)."""
    repo = FakeSlotRepository()
    use_case = UpsertSlot(UpsertSlotDependencies(slots=repo))
    casilla_id = uuid.uuid4()
    original = await use_case.create(
        CreateSlotCommand(
            casilla_id=casilla_id,
            hora_inicio=time(13, 0),
            hora_fin=time(17, 0),
            dia_semana=0,
            sort_order=2,
        )
    )

    updated = await use_case.update(
        UpdateSlotCommand(
            slot_id=original.id,
            hora_inicio=time(13, 30),
            hora_fin=time(17, 30),
            dia_semana=0,
        )
    )

    assert updated.hora_inicio == time(13, 30)
    assert updated.hora_fin == time(17, 30)
    assert updated.sort_order == 2
    assert updated.casilla_id == casilla_id

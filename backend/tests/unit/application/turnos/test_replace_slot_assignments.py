import uuid
from datetime import date

from src.modules.turnos.application.dtos.turno_dtos import ReplaceAssignmentsCommand
from src.modules.turnos.application.use_cases.replace_slot_assignments import (
    ReplaceSlotAssignments,
    ReplaceSlotAssignmentsDependencies,
)
from src.modules.turnos.domain.entities.asignacion import Asignacion
from tests.unit.domain.turnos.fakes import FakeAsignacionRepository


async def test_reasignar_cierra_la_vigencia_anterior_en_vez_de_borrarla() -> None:
    """`vigente_hasta` existe para conservar historial de quién cubrió un slot --
    reasignar operadores no debe hacer hard-delete de la asignación anterior."""
    slot_id = uuid.uuid4()
    old_user = uuid.uuid4()
    repo = FakeAsignacionRepository()
    old_asig = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot_id,
        user_id=old_user,
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    repo.rows[old_asig.id] = old_asig

    use_case = ReplaceSlotAssignments(ReplaceSlotAssignmentsDependencies(asignaciones=repo))
    new_user = uuid.uuid4()
    await use_case.execute(
        ReplaceAssignmentsCommand(
            slot_id=slot_id, user_ids=[new_user], vigente_desde=date(2026, 3, 1)
        )
    )

    closed = repo.rows[old_asig.id]
    assert closed.vigente_hasta == date(2026, 2, 28)
    assert closed.user_id == old_user  # sigue en el historial, no se borró
    new_rows = [a for a in repo.rows.values() if a.user_id == new_user]
    assert len(new_rows) == 1
    assert new_rows[0].vigente_desde == date(2026, 3, 1)
    assert new_rows[0].vigente_hasta is None


async def test_reasignar_el_mismo_dia_borra_en_vez_de_dejar_intervalo_invalido() -> None:
    """Si la asignación anterior arrancó el mismo día que la nueva reemplaza, cerrarla
    dejaría vigente_hasta < vigente_desde -- se borra en vez de dejar un intervalo
    roto, porque nunca llegó a cubrir un día completo."""
    slot_id = uuid.uuid4()
    same_day = date(2026, 3, 1)
    repo = FakeAsignacionRepository()
    same_day_asig = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot_id,
        user_id=uuid.uuid4(),
        vigente_desde=same_day,
        vigente_hasta=None,
    )
    repo.rows[same_day_asig.id] = same_day_asig

    use_case = ReplaceSlotAssignments(ReplaceSlotAssignmentsDependencies(asignaciones=repo))
    await use_case.execute(
        ReplaceAssignmentsCommand(slot_id=slot_id, user_ids=[], vigente_desde=same_day)
    )

    assert same_day_asig.id not in repo.rows


async def test_desasignar_todos_cierra_la_vigencia_sin_insertar_nada() -> None:
    slot_id = uuid.uuid4()
    repo = FakeAsignacionRepository()
    old_asig = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot_id,
        user_id=uuid.uuid4(),
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    repo.rows[old_asig.id] = old_asig

    use_case = ReplaceSlotAssignments(ReplaceSlotAssignmentsDependencies(asignaciones=repo))
    await use_case.execute(
        ReplaceAssignmentsCommand(slot_id=slot_id, user_ids=[], vigente_desde=date(2026, 3, 1))
    )

    assert len(repo.rows) == 1
    assert repo.rows[old_asig.id].vigente_hasta == date(2026, 2, 28)

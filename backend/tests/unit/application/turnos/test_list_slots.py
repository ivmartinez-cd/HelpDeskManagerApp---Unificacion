import uuid
from datetime import date, time

from src.modules.turnos.application.use_cases.list_slots import ListSlots, ListSlotsDependencies
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionRepository,
    FakeSlotRepository,
    FakeUserProvider,
)


def _slot(casilla_id: uuid.UUID, hora_inicio: time) -> Slot:
    return Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=hora_inicio,
        hora_fin=time(hora_inicio.hour + 1),
        dia_semana=0,
        sort_order=0,
    )


async def test_lista_asignaciones_en_un_solo_batch_no_n_mas_1() -> None:
    casilla_id = uuid.uuid4()
    slots_repo = FakeSlotRepository()
    slots = [_slot(casilla_id, time(h)) for h in (8, 11, 13, 15)]
    for s in slots:
        slots_repo.rows[s.id] = s
    asignaciones_repo = FakeAsignacionRepository()

    use_case = ListSlots(
        ListSlotsDependencies(
            slots=slots_repo, asignaciones=asignaciones_repo, users=FakeUserProvider()
        )
    )
    result = await use_case.execute()

    assert len(result) == 4
    assert asignaciones_repo.list_by_slots_calls == 1
    assert asignaciones_repo.list_by_slot_calls == 0


async def test_resuelve_nombre_de_operador_desactivado() -> None:
    """`list_all_active_users()` no debe usarse para resolver nombres -- un
    operador desactivado con una asignación vigente/vieja tiene que seguir
    mostrando su nombre real, no 'Desconocido' (inconsistente con GetCurrentShifts,
    que sí lo resolvía bien)."""
    casilla_id = uuid.uuid4()
    slot = _slot(casilla_id, time(8))
    slots_repo = FakeSlotRepository()
    slots_repo.rows[slot.id] = slot

    user_id = uuid.uuid4()
    asignaciones_repo = FakeAsignacionRepository()
    asig = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=user_id,
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    asignaciones_repo.rows[asig.id] = asig

    users_repo = FakeUserProvider()
    users_repo.users[user_id] = UserInfo(id=user_id, full_name="Operador Desactivado")
    # A propósito NO se agrega a `active_ids` -- simula un usuario deshabilitado.

    use_case = ListSlots(
        ListSlotsDependencies(slots=slots_repo, asignaciones=asignaciones_repo, users=users_repo)
    )
    result = await use_case.execute()

    assert result[0].asignaciones[0].user_name == "Operador Desactivado"

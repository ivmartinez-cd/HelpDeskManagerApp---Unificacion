import uuid
from datetime import date, time

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.services.turno_resolver import TurnoResolver


def test_turno_resolver_identifies_current_and_next_shifts() -> None:
    casilla_id = uuid.uuid4()
    casilla = Casilla(
        id=casilla_id, nombre="INSUMOS", color="#8b5cf6", sort_order=0, is_active=True
    )

    slot1 = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,  # Tuesday
        sort_order=0,
    )
    slot2 = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(11, 0),
        hora_fin=time(13, 0),
        dia_semana=1,
        sort_order=1,
    )

    user1 = uuid.uuid4()
    user2 = uuid.uuid4()

    target_date = date(2026, 8, 11)  # Tuesday
    asig1 = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot1.id,
        user_id=user1,
        vigente_desde=target_date,
        vigente_hasta=None,
    )
    asig2 = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot2.id,
        user_id=user2,
        vigente_desde=target_date,
        vigente_hasta=None,
    )

    resolver = TurnoResolver()
    results = resolver.resolve_shifts(
        casillas=[casilla],
        slots=[slot1, slot2],
        asignaciones=[asig1, asig2],
        target_date=target_date,
        target_time=time(9, 30),
    )

    assert len(results) == 2
    shift1 = next(r for r in results if r.slot_id == slot1.id)
    shift2 = next(r for r in results if r.slot_id == slot2.id)

    assert shift1.is_current is True
    assert shift1.is_next is False
    assert shift1.user_ids == [user1]

    assert shift2.is_current is False
    assert shift2.is_next is True
    assert shift2.user_ids == [user2]

import uuid
from datetime import date, time

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.services.turno_resolver import TurnoResolver
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride


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


def _cobertura(
    ausente: uuid.UUID,
    reemplazante: uuid.UUID,
    *,
    desde: date,
    hasta: date,
    slot_ids: frozenset[uuid.UUID] | None = None,
) -> AsignacionOverride[uuid.UUID, uuid.UUID]:
    return AsignacionOverride(
        id=uuid.uuid4(),
        operador_ausente_id=ausente,
        operador_reemplazante_id=reemplazante,
        desde=desde,
        hasta=hasta,
        alcance="TOTAL" if slot_ids is None else slot_ids,
        estado="ACTIVA",
        motivo=None,
        created_by_user_id=uuid.uuid4(),
    )


def test_resuelve_al_reemplazante_cuando_hay_cobertura_activa_para_la_franja() -> None:
    casilla_id = uuid.uuid4()
    casilla = Casilla(id=casilla_id, nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,
        sort_order=0,
    )
    ausente, reemplazante = uuid.uuid4(), uuid.uuid4()
    target_date = date(2026, 8, 25)
    asignacion = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=ausente,
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    cobertura = _cobertura(
        ausente,
        reemplazante,
        desde=date(2026, 8, 24),
        hasta=date(2026, 8, 28),
        slot_ids=frozenset({slot.id}),
    )

    results = TurnoResolver().resolve_shifts(
        casillas=[casilla],
        slots=[slot],
        asignaciones=[asignacion],
        target_date=target_date,
        target_time=time(9, 0),
        overrides_por_ausente={ausente: [cobertura]},
    )

    assert results[0].user_ids == [reemplazante]


def test_sin_cobertura_activa_muestra_al_operador_original() -> None:
    casilla_id = uuid.uuid4()
    casilla = Casilla(id=casilla_id, nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,
        sort_order=0,
    )
    ausente = uuid.uuid4()
    asignacion = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=ausente,
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )

    results = TurnoResolver().resolve_shifts(
        casillas=[casilla],
        slots=[slot],
        asignaciones=[asignacion],
        target_date=date(2026, 8, 25),
        target_time=time(9, 0),
    )

    assert results[0].user_ids == [ausente]


def test_cobertura_vencida_no_afecta_la_resolucion() -> None:
    casilla_id = uuid.uuid4()
    casilla = Casilla(id=casilla_id, nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,
        sort_order=0,
    )
    ausente, reemplazante = uuid.uuid4(), uuid.uuid4()
    asignacion = Asignacion(
        id=uuid.uuid4(),
        slot_id=slot.id,
        user_id=ausente,
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    cobertura_vencida = _cobertura(
        ausente, reemplazante, desde=date(2026, 8, 3), hasta=date(2026, 8, 7)
    )

    results = TurnoResolver().resolve_shifts(
        casillas=[casilla],
        slots=[slot],
        asignaciones=[asignacion],
        target_date=date(2026, 8, 25),
        target_time=time(9, 0),
        overrides_por_ausente={ausente: [cobertura_vencida]},
    )

    assert results[0].user_ids == [ausente]


def test_dos_titulares_cubiertos_por_la_misma_persona_no_se_duplican() -> None:
    casilla_id = uuid.uuid4()
    casilla = Casilla(id=casilla_id, nombre="INSUMOS", color=None, sort_order=0, is_active=True)
    slot = Slot(
        id=uuid.uuid4(),
        casilla_id=casilla_id,
        hora_inicio=time(8, 0),
        hora_fin=time(11, 0),
        dia_semana=1,
        sort_order=0,
    )
    ausente1, ausente2, reemplazante = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    target_date = date(2026, 8, 25)
    asignaciones = [
        Asignacion(
            id=uuid.uuid4(),
            slot_id=slot.id,
            user_id=ausente1,
            vigente_desde=date(2026, 1, 1),
            vigente_hasta=None,
        ),
        Asignacion(
            id=uuid.uuid4(),
            slot_id=slot.id,
            user_id=ausente2,
            vigente_desde=date(2026, 1, 1),
            vigente_hasta=None,
        ),
    ]
    _desde, _hasta = date(2026, 8, 24), date(2026, 8, 28)
    overrides_por_ausente = {
        ausente1: [_cobertura(ausente1, reemplazante, desde=_desde, hasta=_hasta)],
        ausente2: [_cobertura(ausente2, reemplazante, desde=_desde, hasta=_hasta)],
    }

    results = TurnoResolver().resolve_shifts(
        casillas=[casilla],
        slots=[slot],
        asignaciones=asignaciones,
        target_date=target_date,
        target_time=time(9, 0),
        overrides_por_ausente=overrides_por_ausente,
    )

    assert results[0].user_ids == [reemplazante]

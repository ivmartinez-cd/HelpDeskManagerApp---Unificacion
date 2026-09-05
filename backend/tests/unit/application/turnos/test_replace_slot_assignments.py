import uuid
from datetime import date, time

import pytest

from src.modules.turnos.application.dtos.turno_dtos import ReplaceAssignmentsCommand
from src.modules.turnos.application.use_cases.replace_slot_assignments import (
    ReplaceSlotAssignments,
    ReplaceSlotAssignmentsDependencies,
)
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import SlotNotFoundError, UsuarioNotFoundError
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionRepository,
    FakeSlotRepository,
    FakeUserProvider,
)


class _Escenario:
    """Un slot existente y un proveedor de usuarios al que hay que registrar
    cada operador que se asigne (la FK a `app_user` ahora se valida antes)."""

    def __init__(self) -> None:
        self.asignaciones = FakeAsignacionRepository()
        self.slots = FakeSlotRepository()
        self.users = FakeUserProvider()
        self.slot_id = uuid.uuid4()
        self.slots.rows[self.slot_id] = Slot(
            id=self.slot_id,
            casilla_id=uuid.uuid4(),
            hora_inicio=time(8),
            hora_fin=time(12),
            dia_semana=0,
            sort_order=0,
        )
        self.use_case = ReplaceSlotAssignments(
            ReplaceSlotAssignmentsDependencies(
                asignaciones=self.asignaciones, slots=self.slots, users=self.users
            )
        )

    def usuario(self) -> uuid.UUID:
        uid = uuid.uuid4()
        self.users.users[uid] = UserInfo(id=uid, full_name=f"Operador {uid.hex[:4]}")
        return uid

    def asignacion_abierta(self, user_id: uuid.UUID, desde: date) -> Asignacion:
        asig = Asignacion(
            id=uuid.uuid4(),
            slot_id=self.slot_id,
            user_id=user_id,
            vigente_desde=desde,
            vigente_hasta=None,
        )
        self.asignaciones.rows[asig.id] = asig
        return asig


async def test_reasignar_cierra_la_vigencia_anterior_en_vez_de_borrarla() -> None:
    """`vigente_hasta` existe para conservar historial de quién cubrió un slot --
    reasignar operadores no debe hacer hard-delete de la asignación anterior."""
    esc = _Escenario()
    old_user = esc.usuario()
    old_asig = esc.asignacion_abierta(old_user, date(2026, 1, 1))
    new_user = esc.usuario()

    await esc.use_case.execute(
        ReplaceAssignmentsCommand(
            slot_id=esc.slot_id, user_ids=[new_user], vigente_desde=date(2026, 3, 1)
        )
    )

    closed = esc.asignaciones.rows[old_asig.id]
    assert closed.vigente_hasta == date(2026, 2, 28)
    assert closed.user_id == old_user  # sigue en el historial, no se borró
    new_rows = [a for a in esc.asignaciones.rows.values() if a.user_id == new_user]
    assert len(new_rows) == 1
    assert new_rows[0].vigente_desde == date(2026, 3, 1)
    assert new_rows[0].vigente_hasta is None


async def test_reasignar_el_mismo_dia_borra_en_vez_de_dejar_intervalo_invalido() -> None:
    """Si la asignación anterior arrancó el mismo día que la nueva reemplaza, cerrarla
    dejaría vigente_hasta < vigente_desde -- se borra en vez de dejar un intervalo
    roto, porque nunca llegó a cubrir un día completo."""
    esc = _Escenario()
    same_day = date(2026, 3, 1)
    same_day_asig = esc.asignacion_abierta(esc.usuario(), same_day)

    await esc.use_case.execute(
        ReplaceAssignmentsCommand(slot_id=esc.slot_id, user_ids=[], vigente_desde=same_day)
    )

    assert same_day_asig.id not in esc.asignaciones.rows


async def test_desasignar_todos_cierra_la_vigencia_sin_insertar_nada() -> None:
    esc = _Escenario()
    old_asig = esc.asignacion_abierta(esc.usuario(), date(2026, 1, 1))

    await esc.use_case.execute(
        ReplaceAssignmentsCommand(slot_id=esc.slot_id, user_ids=[], vigente_desde=date(2026, 3, 1))
    )

    assert len(esc.asignaciones.rows) == 1
    assert esc.asignaciones.rows[old_asig.id].vigente_hasta == date(2026, 2, 28)


async def test_operador_repetido_en_user_ids_crea_una_sola_asignacion() -> None:
    """Un mismo operador no puede quedar asignado dos veces al mismo slot -- si
    llega repetido en el comando (ej. estado sucio del frontend), se deduplica."""
    esc = _Escenario()
    user_id = esc.usuario()

    await esc.use_case.execute(
        ReplaceAssignmentsCommand(
            slot_id=esc.slot_id, user_ids=[user_id, user_id], vigente_desde=date(2026, 3, 1)
        )
    )

    rows = [a for a in esc.asignaciones.rows.values() if a.user_id == user_id]
    assert len(rows) == 1


async def test_slot_inexistente_es_not_found_y_no_toca_nada() -> None:
    esc = _Escenario()
    user_id = esc.usuario()

    with pytest.raises(SlotNotFoundError):
        await esc.use_case.execute(
            ReplaceAssignmentsCommand(
                slot_id=uuid.uuid4(), user_ids=[user_id], vigente_desde=date(2026, 3, 1)
            )
        )
    assert esc.asignaciones.rows == {}


async def test_usuario_inexistente_es_not_found_y_no_cierra_la_vigente() -> None:
    """Antes la FK a `app_user` fallaba en el flush (500) después de haber
    cerrado la asignación vigente."""
    esc = _Escenario()
    vigente = esc.asignacion_abierta(esc.usuario(), date(2026, 1, 1))
    fantasma = uuid.uuid4()

    with pytest.raises(UsuarioNotFoundError, match=str(fantasma)):
        await esc.use_case.execute(
            ReplaceAssignmentsCommand(
                slot_id=esc.slot_id, user_ids=[fantasma], vigente_desde=date(2026, 3, 1)
            )
        )
    assert esc.asignaciones.rows[vigente.id].vigente_hasta is None

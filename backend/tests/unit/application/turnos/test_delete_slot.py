import uuid
from datetime import date, time

import pytest

from src.modules.turnos.application.use_cases.delete_slot import DeleteSlot, DeleteSlotDependencies
from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import SlotEnUsoError, SlotNotFoundError
from src.shared.domain.value_objects.asignacion_override import AsignacionOverride
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionOverrideRepository,
    FakeAsignacionRepository,
    FakeSlotRepository,
)


class _Escenario:
    def __init__(self) -> None:
        self.slots = FakeSlotRepository()
        self.asignaciones = FakeAsignacionRepository()
        self.overrides = FakeAsignacionOverrideRepository()
        self.slot = Slot(
            id=uuid.uuid4(),
            casilla_id=uuid.uuid4(),
            hora_inicio=time(8),
            hora_fin=time(12),
            dia_semana=0,
            sort_order=0,
        )
        self.slots.rows[self.slot.id] = self.slot
        self.use_case = DeleteSlot(
            DeleteSlotDependencies(
                slots=self.slots, asignaciones=self.asignaciones, overrides=self.overrides
            )
        )

    def cobertura(
        self, alcance: frozenset[uuid.UUID] | str, estado: str = "ACTIVA"
    ) -> AsignacionOverride[uuid.UUID, uuid.UUID]:
        o: AsignacionOverride[uuid.UUID, uuid.UUID] = AsignacionOverride(
            id=uuid.uuid4(),
            operador_ausente_id=uuid.uuid4(),
            operador_reemplazante_id=uuid.uuid4(),
            desde=date(2026, 9, 1),
            hasta=date(2026, 9, 5),
            alcance=alcance,  # type: ignore[arg-type]
            estado=estado,  # type: ignore[arg-type]
            motivo=None,
            created_by_user_id=uuid.uuid4(),
        )
        self.overrides.rows[o.id] = o
        return o


async def test_borra_la_franja_y_sus_asignaciones() -> None:
    esc = _Escenario()
    asig = Asignacion(
        id=uuid.uuid4(),
        slot_id=esc.slot.id,
        user_id=uuid.uuid4(),
        vigente_desde=date(2026, 1, 1),
        vigente_hasta=None,
    )
    esc.asignaciones.rows[asig.id] = asig

    await esc.use_case.execute(esc.slot.id)

    assert esc.slots.rows == {}
    assert esc.asignaciones.rows == {}


async def test_franja_inexistente_es_not_found() -> None:
    esc = _Escenario()

    with pytest.raises(SlotNotFoundError):
        await esc.use_case.execute(uuid.uuid4())


async def test_cobertura_parcial_activa_que_la_referencia_bloquea_el_borrado() -> None:
    """El CASCADE de `turno_asignacion_override_slot` dejaría la cobertura con
    alcance vacío: dejaría de cubrir sin aviso."""
    esc = _Escenario()
    cobertura = esc.cobertura(frozenset({esc.slot.id}))

    with pytest.raises(SlotEnUsoError, match=str(cobertura.id)):
        await esc.use_case.execute(esc.slot.id)
    assert esc.slot.id in esc.slots.rows


async def test_coberturas_canceladas_totales_o_de_otra_franja_no_bloquean() -> None:
    esc = _Escenario()
    esc.cobertura(frozenset({esc.slot.id}), estado="CANCELADA")
    esc.cobertura("TOTAL")
    esc.cobertura(frozenset({uuid.uuid4()}))

    await esc.use_case.execute(esc.slot.id)

    assert esc.slots.rows == {}

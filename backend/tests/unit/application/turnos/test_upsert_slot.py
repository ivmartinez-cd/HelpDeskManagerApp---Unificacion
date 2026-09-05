import uuid
from datetime import time

import pytest

from src.modules.turnos.application.dtos.turno_dtos import CreateSlotCommand, UpdateSlotCommand
from src.modules.turnos.application.use_cases.upsert_slot import (
    UpsertSlot,
    UpsertSlotDependencies,
)
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.errors import (
    CasillaNotFoundError,
    FranjaInvalidaError,
    FranjasSolapadasError,
    SlotNotFoundError,
)
from tests.unit.domain.turnos.fakes import FakeCasillaRepository, FakeSlotRepository


class _Escenario:
    def __init__(self) -> None:
        self.slots = FakeSlotRepository()
        self.casillas = FakeCasillaRepository()
        self.casilla = Casilla(
            id=uuid.uuid4(), nombre="INSUMOS", color=None, sort_order=0, is_active=True
        )
        self.casillas.rows[self.casilla.id] = self.casilla
        self.use_case = UpsertSlot(UpsertSlotDependencies(slots=self.slots, casillas=self.casillas))

    def crear(
        self, inicio: time, fin: time, dia: int = 0, *, casilla_id: uuid.UUID | None = None
    ) -> CreateSlotCommand:
        return CreateSlotCommand(
            casilla_id=casilla_id or self.casilla.id,
            hora_inicio=inicio,
            hora_fin=fin,
            dia_semana=dia,
            sort_order=2,
        )


async def test_update_preserva_sort_order_al_editar_horario() -> None:
    """La UI solo edita hora_inicio/hora_fin/dia_semana -- el PUT no debe resetear
    sort_order a 0 (bug real: la tercera franja del día perdía su posición de
    despliegue apenas se le tocaba el horario)."""
    esc = _Escenario()
    original = await esc.use_case.create(esc.crear(time(13, 0), time(17, 0)))

    updated = await esc.use_case.update(
        UpdateSlotCommand(
            slot_id=original.id, hora_inicio=time(13, 30), hora_fin=time(17, 30), dia_semana=0
        )
    )

    assert updated.hora_inicio == time(13, 30)
    assert updated.hora_fin == time(17, 30)
    assert updated.sort_order == 2
    assert updated.casilla_id == esc.casilla.id


async def test_crear_en_casilla_inexistente_es_404_no_500() -> None:
    esc = _Escenario()

    with pytest.raises(CasillaNotFoundError):
        await esc.use_case.create(esc.crear(time(8), time(9), casilla_id=uuid.uuid4()))
    assert esc.slots.rows == {}


async def test_update_de_franja_inexistente_es_not_found() -> None:
    esc = _Escenario()

    with pytest.raises(SlotNotFoundError):
        await esc.use_case.update(
            UpdateSlotCommand(
                slot_id=uuid.uuid4(), hora_inicio=time(8), hora_fin=time(9), dia_semana=0
            )
        )


async def test_hora_inicio_mayor_o_igual_que_fin_se_rechaza() -> None:
    esc = _Escenario()

    with pytest.raises(FranjaInvalidaError, match="20:00-19:00"):
        await esc.use_case.create(esc.crear(time(20), time(19)))
    with pytest.raises(FranjaInvalidaError):
        await esc.use_case.create(esc.crear(time(8), time(8)))


async def test_dia_semana_fuera_de_rango_se_rechaza() -> None:
    esc = _Escenario()

    with pytest.raises(FranjaInvalidaError, match="fuera de 0..6"):
        await esc.use_case.create(esc.crear(time(8), time(9), dia=7))


async def test_solape_con_otra_franja_de_la_misma_casilla_y_dia_es_conflicto() -> None:
    esc = _Escenario()
    await esc.use_case.create(esc.crear(time(8), time(12)))

    with pytest.raises(FranjasSolapadasError, match="08:00-12:00 y 11:00-13:00"):
        await esc.use_case.create(esc.crear(time(11), time(13)))
    assert len(esc.slots.rows) == 1


async def test_franjas_contiguas_o_de_otro_dia_no_solapan() -> None:
    esc = _Escenario()
    await esc.use_case.create(esc.crear(time(8), time(12)))

    await esc.use_case.create(esc.crear(time(12), time(13)))  # borde compartido
    await esc.use_case.create(esc.crear(time(8), time(12), dia=1))  # otro día

    assert len(esc.slots.rows) == 3


async def test_editar_una_franja_no_solapa_consigo_misma() -> None:
    esc = _Escenario()
    creada = await esc.use_case.create(esc.crear(time(8), time(12)))

    updated = await esc.use_case.update(
        UpdateSlotCommand(
            slot_id=creada.id, hora_inicio=time(8, 30), hora_fin=time(12), dia_semana=0
        )
    )

    assert updated.hora_inicio == time(8, 30)


async def test_editar_una_franja_encima_de_otra_es_conflicto() -> None:
    esc = _Escenario()
    await esc.use_case.create(esc.crear(time(8), time(12)))
    tarde = await esc.use_case.create(esc.crear(time(13), time(17)))

    with pytest.raises(FranjasSolapadasError):
        await esc.use_case.update(
            UpdateSlotCommand(
                slot_id=tarde.id, hora_inicio=time(11), hora_fin=time(17), dia_semana=0
            )
        )

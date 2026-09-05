import uuid
from datetime import date, time

import pytest

from src.modules.turnos.application.use_cases.delete_casilla import (
    DeleteCasilla,
    DeleteCasillaDependencies,
)
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.domain.entities.slot import Slot
from src.modules.turnos.domain.errors import CasillaEnUsoError, CasillaNotFoundError
from tests.unit.domain.turnos.fakes import (
    FakeCasillaRepository,
    FakeGrillaVarianteRepository,
    FakeSlotRepository,
)


class _Escenario:
    def __init__(self) -> None:
        self.casillas = FakeCasillaRepository()
        self.slots = FakeSlotRepository()
        self.variantes = FakeGrillaVarianteRepository()
        self.casilla = Casilla(
            id=uuid.uuid4(), nombre="INSUMOS", color=None, sort_order=0, is_active=True
        )
        self.casillas.rows[self.casilla.id] = self.casilla
        self.use_case = DeleteCasilla(
            DeleteCasillaDependencies(
                casillas=self.casillas, slots=self.slots, variantes=self.variantes
            )
        )

    def franja_titular(self) -> None:
        slot = Slot(
            id=uuid.uuid4(),
            casilla_id=self.casilla.id,
            hora_inicio=time(8),
            hora_fin=time(12),
            dia_semana=0,
            sort_order=0,
        )
        self.slots.rows[slot.id] = slot

    def variante(self, estado: str, casilla_id: uuid.UUID) -> None:
        v = GrillaVariante(
            id=uuid.uuid4(),
            motivo="Vacaciones Majo",
            origen_texto=None,
            desde=date(2026, 8, 24),
            hasta=date(2026, 8, 28),
            estado=estado,  # type: ignore[arg-type]
            created_by_user_id=uuid.uuid4(),
            slots=[
                VarianteSlot(
                    id=uuid.uuid4(),
                    casilla_id=casilla_id,
                    dia_semana=0,
                    hora_inicio=time(8),
                    hora_fin=time(9),
                    sort_order=0,
                )
            ],
        )
        self.variantes.rows[v.id] = v


async def test_borra_una_casilla_sin_referencias() -> None:
    esc = _Escenario()

    await esc.use_case.execute(esc.casilla.id)

    assert esc.casillas.rows == {}


async def test_casilla_inexistente_es_not_found() -> None:
    esc = _Escenario()

    with pytest.raises(CasillaNotFoundError):
        await esc.use_case.execute(uuid.uuid4())


async def test_con_franjas_titulares_se_rechaza() -> None:
    esc = _Escenario()
    esc.franja_titular()

    with pytest.raises(CasillaEnUsoError, match="1 franja"):
        await esc.use_case.execute(esc.casilla.id)
    assert esc.casilla.id in esc.casillas.rows


async def test_referenciada_por_grilla_de_vacaciones_activa_se_rechaza() -> None:
    """El CASCADE de `turno_grilla_variante_slot.casilla_id` vaciaría una
    variante ACTIVA, violando el invariante que el alta sí exige."""
    esc = _Escenario()
    esc.variante("ACTIVA", esc.casilla.id)

    with pytest.raises(CasillaEnUsoError, match="Vacaciones Majo"):
        await esc.use_case.execute(esc.casilla.id)


async def test_variantes_canceladas_o_de_otra_casilla_no_bloquean() -> None:
    esc = _Escenario()
    esc.variante("CANCELADA", esc.casilla.id)
    esc.variante("ACTIVA", uuid.uuid4())

    await esc.use_case.execute(esc.casilla.id)

    assert esc.casillas.rows == {}

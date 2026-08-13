import uuid

from src.modules.liquidaciones.application.use_cases.list_liquidaciones import (
    ListLiquidaciones,
    ListLiquidacionesPorts,
)
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes import FakeLiquidacionRepository


async def test_sin_filtros_devuelve_todas() -> None:
    repo = FakeLiquidacionRepository()
    liq_a = make_liquidacion()
    liq_b = make_liquidacion(prestador_id=uuid.uuid4())
    repo.rows[liq_a.id] = liq_a
    repo.rows[liq_b.id] = liq_b

    resultado = await ListLiquidaciones(ListLiquidacionesPorts(liquidaciones=repo)).execute()

    assert {liq.id for liq in resultado} == {liq_a.id, liq_b.id}


async def test_con_prestador_filtra_por_prestador() -> None:
    repo = FakeLiquidacionRepository()
    prestador_id = uuid.uuid4()
    propia = make_liquidacion(prestador_id=prestador_id)
    ajena = make_liquidacion(prestador_id=uuid.uuid4())
    repo.rows[propia.id] = propia
    repo.rows[ajena.id] = ajena

    resultado = await ListLiquidaciones(ListLiquidacionesPorts(liquidaciones=repo)).execute(
        prestador_id=prestador_id
    )

    assert [liq.id for liq in resultado] == [propia.id]


async def test_con_estado_filtra_por_estado() -> None:
    repo = FakeLiquidacionRepository()
    abierta = make_liquidacion()
    aprobada = make_liquidacion(estado="aprobada")
    repo.rows[abierta.id] = abierta
    repo.rows[aprobada.id] = aprobada

    resultado = await ListLiquidaciones(ListLiquidacionesPorts(liquidaciones=repo)).execute(
        estado="aprobada"
    )

    assert [liq.id for liq in resultado] == [aprobada.id]


async def test_con_periodo_filtra_por_periodo() -> None:
    repo = FakeLiquidacionRepository()
    enero = make_liquidacion(periodo="2026-01")
    febrero = make_liquidacion(periodo="2026-02")
    repo.rows[enero.id] = enero
    repo.rows[febrero.id] = febrero

    resultado = await ListLiquidaciones(ListLiquidacionesPorts(liquidaciones=repo)).execute(
        periodo="2026-01"
    )

    assert [liq.id for liq in resultado] == [enero.id]

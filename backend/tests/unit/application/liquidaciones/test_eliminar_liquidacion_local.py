"""Tests de EliminarLiquidacionLocal — DELETE /{id} no puede borrar sin más una
liquidación vinculada a Canal Directo (desincroniza local vs. AyC); `forzar`
es la única excepción, reservada al link "Eliminar solo localmente" tras un
`/anular` que ya falló."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.eliminar_liquidacion_local import (
    EliminarLiquidacionLocal,
    EliminarLiquidacionLocalPorts,
)
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.exceptions import LiquidacionConVinculoAycError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.use_case = EliminarLiquidacionLocal(
            EliminarLiquidacionLocalPorts(liquidaciones=self.liquidaciones)
        )


async def test_liquidacion_no_encontrada_lanza_not_found() -> None:
    world = World()

    with pytest.raises(LiquidacionNoEncontradaError):
        await world.use_case.execute(uuid.uuid4())


async def test_liquidacion_sin_vinculo_ayc_se_borra_directo() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion=None)
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id)

    assert liq.id not in world.liquidaciones.rows


async def test_liquidacion_con_vinculo_ayc_rechaza_sin_forzar() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3894-2")
    world.liquidaciones.rows[liq.id] = liq

    with pytest.raises(LiquidacionConVinculoAycError):
        await world.use_case.execute(liq.id)

    # no se borró nada
    assert liq.id in world.liquidaciones.rows


async def test_liquidacion_con_vinculo_ayc_se_borra_si_se_fuerza() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3894-2")
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id, forzar=True)

    assert liq.id not in world.liquidaciones.rows

"""Tests de AnularLiquidacion — anula en wsAyC (voidLiquidation) y elimina registro local.

Orden crítico: SOAP primero, delete después. Si el SOAP falla el registro local queda intacto.
"""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.anular_liquidacion import (
    AnularLiquidacion,
    AnularLiquidacionPorts,
)
from src.modules.liquidaciones.domain.exceptions import (
    LiquidacionAyCOperationError,
    LiquidacionSinVinculoAyCError,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes import FakeCdLiquidacionesGateway
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.gateway = FakeCdLiquidacionesGateway()
        self.use_case = AnularLiquidacion(
            AnularLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                cd_gateway=self.gateway,
            )
        )


async def test_liquidacion_no_encontrada_lanza_not_found() -> None:
    world = World()
    with pytest.raises(NotFoundError):
        await world.use_case.execute(uuid.uuid4())


async def test_sin_vinculo_ayc_lanza_error() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion=None)
    world.liquidaciones.rows[liq.id] = liq
    with pytest.raises(LiquidacionSinVinculoAyCError):
        await world.use_case.execute(liq.id)


async def test_anulacion_llama_void_y_elimina_registro_local() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="777-4")
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id)

    assert world.gateway.anulados == [777]
    assert liq.id not in world.liquidaciones.rows


async def test_pasa_ayc_id_correcto_al_void() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="12345-1")
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id)

    assert world.gateway.anulados == [12345]


async def test_fallo_soap_no_elimina_local() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="777-4")
    world.liquidaciones.rows[liq.id] = liq
    world.gateway.void_raises = RuntimeError("voidLiquidation retornó false")

    with pytest.raises(LiquidacionAyCOperationError):
        await world.use_case.execute(liq.id)

    assert liq.id in world.liquidaciones.rows

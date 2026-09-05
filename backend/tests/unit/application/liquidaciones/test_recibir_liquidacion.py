"""Tests de RecibirLiquidacion — propaga estado "Recibida" a wsAyC y actualiza local.
La mecánica compartida (not found, sin vínculo, fallo SOAP) la cubre
test_observar_liquidacion sobre la misma base `PropagarEstadoAyC`."""

import pytest

from src.modules.liquidaciones.application.use_cases.recibir_liquidacion import (
    RecibirLiquidacion,
    RecibirLiquidacionPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_RECIBIDA
from src.modules.liquidaciones.domain.exceptions import (
    LiquidacionAyCOperationError,
    TransicionEstadoAycInvalidaError,
)
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes import FakeCdLiquidacionesGateway
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.gateway = FakeCdLiquidacionesGateway()
        self.use_case = RecibirLiquidacion(
            RecibirLiquidacionPorts(liquidaciones=self.liquidaciones, cd_gateway=self.gateway)
        )


async def test_recibir_escribe_recibida_en_ayc_y_local() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3936-7", estado="preliquidada")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Juan Pérez")

    assert resultado.estado == ESTADO_RECIBIDA
    assert world.liquidaciones.rows[liq.id].estado == ESTADO_RECIBIDA
    assert world.gateway.estados_seteados == [(3936, ESTADO_RECIBIDA, "Juan Pérez")]


async def test_recibir_desde_observada_tambien_vale() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3936-8", estado="observada")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Juan Pérez")

    assert resultado.estado == ESTADO_RECIBIDA


async def test_desde_estado_invalido_rechaza_sin_pegarle_a_soap() -> None:
    """Mismo criterio que Web Agentes: el botón "Recibir" no existe si el
    estado no es Preliquidada/Observada."""
    world = World()
    liq = make_liquidacion(numero_liquidacion="3936-9", estado="aprobada")
    world.liquidaciones.rows[liq.id] = liq

    with pytest.raises(TransicionEstadoAycInvalidaError):
        await world.use_case.execute(liq.id, "Operador")

    assert world.gateway.estados_seteados == []


async def test_fallo_soap_no_escribe_local_y_nombra_la_accion() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-0", estado="preliquidada")
    world.liquidaciones.rows[liq.id] = liq
    world.gateway.set_estado_raises = RuntimeError("SOAP caído")

    with pytest.raises(LiquidacionAyCOperationError, match="No se pudo recibir"):
        await world.use_case.execute(liq.id, "Operador")

    assert world.liquidaciones.rows[liq.id].estado == "preliquidada"

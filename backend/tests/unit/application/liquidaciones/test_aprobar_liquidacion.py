"""Tests de AprobarLiquidacion — propaga estado "Aprobada" a wsAyC y actualiza local.

Orden crítico: SOAP primero, DB después. Si el SOAP falla no hay escritura local.
"""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.aprobar_liquidacion import (
    AprobarLiquidacion,
    AprobarLiquidacionPorts,
)
from src.modules.liquidaciones.domain.exceptions import (
    LiquidacionAyCOperationError,
    LiquidacionSinVinculoAyCError,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes import (
    FakeCdLiquidacionesGateway,
    FakeLiquidacionRepository,
)


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.gateway = FakeCdLiquidacionesGateway()
        self.use_case = AprobarLiquidacion(
            AprobarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                cd_gateway=self.gateway,
            )
        )


async def test_liquidacion_no_encontrada_lanza_not_found() -> None:
    world = World()
    with pytest.raises(NotFoundError):
        await world.use_case.execute(uuid.uuid4(), "Operador")


async def test_sin_vinculo_ayc_lanza_error() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion=None)
    world.liquidaciones.rows[liq.id] = liq
    with pytest.raises(LiquidacionSinVinculoAyCError):
        await world.use_case.execute(liq.id, "Operador")


async def test_aprobacion_actualiza_estado_local_a_aprobada() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-0", estado="abierta")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Juan Pérez")

    assert resultado.estado == "aprobada"
    assert world.liquidaciones.rows[liq.id].estado == "aprobada"


async def test_pasa_ayc_id_y_usuario_correctos_al_soap() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="999-3")
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id, "Ana García")

    assert len(world.gateway.estados_seteados) == 1
    ayc_id, estado_ayc, usuario = world.gateway.estados_seteados[0]
    assert ayc_id == 999
    assert estado_ayc == "Aprobada"
    assert usuario == "Ana García"


async def test_fallo_soap_no_escribe_local() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-0", estado="abierta")
    world.liquidaciones.rows[liq.id] = liq
    world.gateway.set_estado_raises = RuntimeError("Timeout SOAP")

    with pytest.raises(LiquidacionAyCOperationError):
        await world.use_case.execute(liq.id, "Operador")

    assert world.liquidaciones.rows[liq.id].estado == "abierta"

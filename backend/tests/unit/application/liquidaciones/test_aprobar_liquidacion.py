"""Tests de AprobarLiquidacion — propaga estado "Aprobada" a wsAyC y actualiza local.

Orden crítico: SOAP primero, DB después. Si el SOAP falla no hay escritura local.
"""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.aprobar_liquidacion import (
    AprobarLiquidacion,
    AprobarLiquidacionPorts,
)
from src.modules.liquidaciones.domain.entities.liquidacion import ESTADO_APROBADA
from src.modules.liquidaciones.domain.exceptions import (
    LiquidacionAyCOperationError,
    LiquidacionSinVinculoAyCError,
    TransicionEstadoAycInvalidaError,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes import FakeCdLiquidacionesGateway, FakeNotificador
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.gateway = FakeCdLiquidacionesGateway()
        self.notificador = FakeNotificador()
        self.use_case = AprobarLiquidacion(
            AprobarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                cd_gateway=self.gateway,
                notificador=self.notificador,
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
    liq = make_liquidacion(numero_liquidacion="500-0", estado="recibida")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Juan Pérez")

    assert resultado.estado == "aprobada"
    assert world.liquidaciones.rows[liq.id].estado == "aprobada"


async def test_aprobar_desde_observada_tambien_vale() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-1", estado="observada")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Juan Pérez")

    assert resultado.estado == "aprobada"


async def test_desde_estado_invalido_rechaza_sin_pegarle_a_soap() -> None:
    """Mismo criterio que Web Agentes: el botón "Aprobar" no existe si el
    estado no es Recibida/Observada."""
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-2", estado="preliquidada")
    world.liquidaciones.rows[liq.id] = liq

    with pytest.raises(TransicionEstadoAycInvalidaError):
        await world.use_case.execute(liq.id, "Operador")

    assert world.gateway.estados_seteados == []
    assert world.notificador.aprobaciones == []


async def test_pasa_ayc_id_y_usuario_correctos_al_soap() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="999-3", estado="recibida")
    world.liquidaciones.rows[liq.id] = liq

    await world.use_case.execute(liq.id, "Ana García")

    assert len(world.gateway.estados_seteados) == 1
    ayc_id, estado_ayc, usuario = world.gateway.estados_seteados[0]
    assert ayc_id == 999
    assert estado_ayc == ESTADO_APROBADA
    assert usuario == "Ana García"


async def test_fallo_soap_no_escribe_local() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="500-0", estado="recibida")
    world.liquidaciones.rows[liq.id] = liq
    world.gateway.set_estado_raises = RuntimeError("Timeout SOAP")

    with pytest.raises(LiquidacionAyCOperationError):
        await world.use_case.execute(liq.id, "Operador")

    assert world.liquidaciones.rows[liq.id].estado == "recibida"
    assert world.notificador.aprobaciones == []


async def test_aprobacion_exitosa_dispara_notificacion() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3938-5", estado="recibida")
    world.liquidaciones.rows[liq.id] = liq

    resultado = await world.use_case.execute(liq.id, "Operador")

    assert len(world.notificador.aprobaciones) == 1
    notificada = world.notificador.aprobaciones[0]
    assert notificada.id == liq.id
    assert notificada.numero_liquidacion == "3938-5"
    assert notificada.estado == resultado.estado == "aprobada"

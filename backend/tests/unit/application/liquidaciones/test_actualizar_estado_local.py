"""Tests de ActualizarEstadoLocal — el PATCH /{id}/estado solo puede tocar
liquidaciones sin vínculo AyC; las vinculadas quedan gobernadas por la
reconciliación (ADR-024) y los botones Aprobar/Observar/Anular."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.actualizar_estado_local import (
    ActualizarEstadoLocal,
    ActualizarEstadoLocalPorts,
)
from src.modules.liquidaciones.domain.exceptions import LiquidacionConVinculoAycError
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.use_case = ActualizarEstadoLocal(
            ActualizarEstadoLocalPorts(liquidaciones=self.liquidaciones)
        )


async def test_liquidacion_no_encontrada_lanza_not_found() -> None:
    world = World()

    with pytest.raises(NotFoundError):
        await world.use_case.execute(uuid.uuid4(), "aprobada")


async def test_liquidacion_con_vinculo_ayc_no_se_puede_cambiar_a_mano() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion="3894-2", estado="observada")
    world.liquidaciones.rows[liq.id] = liq

    with pytest.raises(LiquidacionConVinculoAycError):
        await world.use_case.execute(liq.id, "aprobada")

    # no se tocó nada
    assert world.liquidaciones.rows[liq.id].estado == "observada"


async def test_liquidacion_sin_vinculo_ayc_cambia_de_estado() -> None:
    world = World()
    liq = make_liquidacion(numero_liquidacion=None, estado="abierta")
    world.liquidaciones.rows[liq.id] = liq

    updated = await world.use_case.execute(liq.id, "preliquidada")

    assert updated.estado == "preliquidada"
    assert world.liquidaciones.rows[liq.id].estado == "preliquidada"

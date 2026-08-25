"""Tests de ActualizarExtraLiquidacion — el PATCH /{id}/extra recalcula
total_importe para que el ítem extra quede reflejado ahí (hallazgo 2026-08-25,
liquidación 3907-5: el extra cargado no se veía en listado/dashboard)."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.actualizar_extra_liquidacion import (
    ActualizarExtraLiquidacion,
    ActualizarExtraLiquidacionPorts,
)
from src.shared.domain.errors import NotFoundError
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.use_case = ActualizarExtraLiquidacion(
            ActualizarExtraLiquidacionPorts(liquidaciones=self.liquidaciones)
        )


async def test_liquidacion_no_encontrada_lanza_not_found() -> None:
    world = World()

    with pytest.raises(NotFoundError):
        await world.use_case.execute(uuid.uuid4(), "Adicional", 500.0)


async def test_cargar_extra_suma_al_total_importe() -> None:
    world = World()
    liq = make_liquidacion(total_importe=113.0, total_incidentes=1)
    world.liquidaciones.rows[liq.id] = liq

    updated = await world.use_case.execute(liq.id, "Viáticos", 500.0)

    assert updated.concepto_extra == "Viáticos"
    assert updated.monto_extra == 500.0
    assert updated.total_importe == 613.0
    assert world.liquidaciones.rows[liq.id].total_importe == 613.0


async def test_cambiar_el_monto_de_un_extra_existente_ajusta_por_delta() -> None:
    world = World()
    liq = make_liquidacion(
        total_importe=613.0, total_incidentes=1, concepto_extra="Viáticos", monto_extra=500.0
    )
    world.liquidaciones.rows[liq.id] = liq

    updated = await world.use_case.execute(liq.id, "Viáticos", 300.0)

    assert updated.monto_extra == 300.0
    assert updated.total_importe == 413.0


async def test_borrar_el_extra_resta_del_total_importe() -> None:
    world = World()
    liq = make_liquidacion(
        total_importe=613.0, total_incidentes=1, concepto_extra="Viáticos", monto_extra=500.0
    )
    world.liquidaciones.rows[liq.id] = liq

    updated = await world.use_case.execute(liq.id, None, None)

    assert updated.concepto_extra is None
    assert updated.monto_extra is None
    assert updated.total_importe == 113.0

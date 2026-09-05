"""Tests de ReanalizarLiquidacionesAbiertas — reanálisis automático tras un cambio
de configuración: solo las no terminales, filtrable por prestador."""

import uuid

import pytest

from src.modules.liquidaciones.application.dtos.reanalizar_liquidacion import (
    ReanalizarLiquidacionResultado,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidaciones_abiertas import (
    ReanalizarLiquidacionesAbiertas,
    ReanalizarLiquidacionesAbiertasPorts,
)
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository

pytestmark = pytest.mark.asyncio


class _ReanalizarSpy:
    def __init__(self) -> None:
        self.ids: list[uuid.UUID] = []

    async def execute(self, liquidacion_id: uuid.UUID) -> ReanalizarLiquidacionResultado:
        self.ids.append(liquidacion_id)
        return ReanalizarLiquidacionResultado(total_incidentes=10, total_alertas=3)


def _caso(*liqs) -> tuple[ReanalizarLiquidacionesAbiertas, _ReanalizarSpy]:
    repo = FakeLiquidacionRepository()
    for liq in liqs:
        repo.rows[liq.id] = liq
    spy = _ReanalizarSpy()
    ports = ReanalizarLiquidacionesAbiertasPorts(liquidaciones=repo, reanalizar=spy)  # type: ignore[arg-type]
    return ReanalizarLiquidacionesAbiertas(ports), spy


async def test_reanaliza_solo_las_no_terminales_del_prestador() -> None:
    prestador = uuid.uuid4()
    abierta = make_liquidacion(prestador_id=prestador, estado="recibida")
    observada = make_liquidacion(prestador_id=prestador, estado="observada")
    aprobada = make_liquidacion(prestador_id=prestador, estado="aprobada")
    cerrada = make_liquidacion(prestador_id=prestador, estado="cerrada")
    de_otro = make_liquidacion(estado="preliquidada")
    uc, spy = _caso(abierta, observada, aprobada, cerrada, de_otro)

    resultado = await uc.execute(prestador)

    assert set(spy.ids) == {abierta.id, observada.id}
    assert resultado.reanalizadas == 2
    assert resultado.total_alertas == 6


async def test_sin_prestador_reanaliza_todas_las_abiertas() -> None:
    a = make_liquidacion(estado="preliquidada")
    b = make_liquidacion(estado="recibida")
    c = make_liquidacion(estado="cerrada")
    uc, spy = _caso(a, b, c)

    resultado = await uc.execute(None)

    assert set(spy.ids) == {a.id, b.id}
    assert resultado.reanalizadas == 2


async def test_sin_abiertas_no_llama_al_motor() -> None:
    uc, spy = _caso(make_liquidacion(estado="cerrada"))

    resultado = await uc.execute(None)

    assert spy.ids == []
    assert resultado.reanalizadas == 0

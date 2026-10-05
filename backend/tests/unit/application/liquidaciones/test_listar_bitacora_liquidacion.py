"""Tests de ListarBitacoraLiquidacion — el hilo se pide a Siges por el número
de CD sin dígito verificador; sin número local no hay hilo."""

import uuid
from datetime import datetime

import pytest

from src.modules.liquidaciones.application.use_cases.listar_bitacora_liquidacion import (
    ListarBitacoraLiquidacion,
)
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from src.modules.liquidaciones.domain.repositories.bitacora_gateway import (
    ComentarioBitacora,
    EntradaBitacora,
)
from tests.unit.domain.liquidaciones.factories import make_liquidacion
from tests.unit.domain.liquidaciones.fakes_liquidacion import FakeLiquidacionRepository

_ENTRADA = EntradaBitacora(
    id_consulta=226865,
    fecha=datetime(2026, 10, 2, 11, 41),
    usuario="marodriguez",
    autor="Mariana Rodriguez",
    es_canal=True,
    texto="Está correcta",
)


class FakeBitacora:
    def __init__(self) -> None:
        self.pedidos: list[int] = []

    async def comentarios_pst_recientes(self, horas: int) -> list[ComentarioBitacora]:
        return []

    async def hilo_de_liquidacion(self, numero_liquidacion_cd: int) -> list[EntradaBitacora]:
        self.pedidos.append(numero_liquidacion_cd)
        return [_ENTRADA]


def _caso(numero: str | None) -> tuple[ListarBitacoraLiquidacion, FakeBitacora, uuid.UUID]:
    liquidaciones = FakeLiquidacionRepository()
    liq = make_liquidacion(numero_liquidacion=numero)
    liquidaciones.rows[liq.id] = liq
    bitacora = FakeBitacora()
    return ListarBitacoraLiquidacion(liquidaciones, bitacora), bitacora, liq.id


async def test_pide_el_hilo_por_numero_cd_sin_digito_verificador() -> None:
    caso, bitacora, liq_id = _caso("3984-4")

    assert await caso.execute(liq_id) == [_ENTRADA]
    assert bitacora.pedidos == [3984]


async def test_sin_numero_de_liquidacion_no_consulta_siges() -> None:
    caso, bitacora, liq_id = _caso(None)

    assert await caso.execute(liq_id) == []
    assert bitacora.pedidos == []


async def test_liquidacion_inexistente() -> None:
    caso, _, _ = _caso("3984-4")

    with pytest.raises(LiquidacionNoEncontradaError):
        await caso.execute(uuid.uuid4())

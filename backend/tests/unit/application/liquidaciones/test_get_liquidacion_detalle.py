"""Tests de GetLiquidacionDetalle — en particular el enriquecimiento de incidentes
con la fila de tabla KM que matchea por sucursal (localidad/SPST/url de Maps)."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.get_liquidacion_detalle import (
    GetLiquidacionDetalle,
    GetLiquidacionDetallePorts,
)
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from tests.unit.domain.liquidaciones.factories import (
    make_incidente,
    make_liquidacion,
    make_tabla_km,
)
from tests.unit.domain.liquidaciones.fakes import FakeTablaKmRepository
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
    FakeLiquidacionRepository,
)


def _armar(liquidaciones=None, incidentes=None, tabla_km=None) -> GetLiquidacionDetalle:
    liq_repo = FakeLiquidacionRepository()
    for liq in liquidaciones or []:
        liq_repo.rows[liq.id] = liq
    inc_repo = FakeIncidenteRepository()
    for inc in incidentes or []:
        inc_repo.rows[inc.id] = inc
    return GetLiquidacionDetalle(
        GetLiquidacionDetallePorts(
            liquidaciones=liq_repo,
            incidentes=inc_repo,
            alertas=FakeAlertaRepository(),
            tablas_km=FakeTablaKmRepository(tabla_km or []),
        )
    )


class TestGetLiquidacionDetalle:
    async def test_liquidacion_inexistente_lanza_error(self) -> None:
        with pytest.raises(LiquidacionNoEncontradaError):
            await _armar().execute(uuid.uuid4())

    async def test_enriquece_incidente_con_fila_de_tabla_km(self) -> None:
        liq = make_liquidacion()
        spst_id = uuid.uuid4()
        fila = make_tabla_km(
            prestador_id=liq.prestador_id,
            sucursal_nombre="Sucursal Centro",
            localidad_cliente="San Juan",
            spst_id=spst_id,
            url_maps="https://maps.google.com/?q=x",
        )
        inc = make_incidente(liquidacion_id=liq.id, sucursal_nombre="  sucursal centro ")

        detalle = await _armar([liq], [inc], [fila]).execute(liq.id)

        assert len(detalle.incidentes) == 1
        enriquecido = detalle.incidentes[0]
        assert enriquecido.incidente.id == inc.id
        assert enriquecido.localidad_cliente == "San Juan"
        assert enriquecido.spst_id == spst_id
        assert enriquecido.url_maps == "https://maps.google.com/?q=x"

    async def test_sin_match_en_tabla_km_deja_campos_en_none(self) -> None:
        liq = make_liquidacion()
        inc = make_incidente(liquidacion_id=liq.id, sucursal_nombre="Otra Sucursal")

        detalle = await _armar([liq], [inc]).execute(liq.id)

        assert detalle.incidentes[0].localidad_cliente is None
        assert detalle.incidentes[0].spst_id is None
        assert detalle.incidentes[0].url_maps is None

    async def test_no_matchea_por_sucursal_si_la_empresa_es_distinta(self) -> None:
        """Antes indexaba solo por sucursal: dos empresas con sucursal homónima
        (ej. "Neuquen") hacían que una "tomara prestado" el SPST de la otra."""
        liq = make_liquidacion()
        fila = make_tabla_km(
            prestador_id=liq.prestador_id,
            empresa_nombre="Calico",
            sucursal_nombre="Neuquen",
            localidad_cliente="Centenario",
            spst_id=uuid.uuid4(),
        )
        inc = make_incidente(
            liquidacion_id=liq.id, empresa_nombre="OCA", sucursal_nombre="Neuquen"
        )

        detalle = await _armar([liq], [inc], [fila]).execute(liq.id)

        assert detalle.incidentes[0].localidad_cliente is None
        assert detalle.incidentes[0].spst_id is None

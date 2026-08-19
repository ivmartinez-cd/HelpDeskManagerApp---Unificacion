"""EvaluarTier0Geovalidacion: worklist de saneo geométrico, cero llamadas."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier0 import (
    EvaluarTier0Geovalidacion,
    GeovalidacionTier0Ports,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
    SigesSucursalPropia,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import FakeSigesGeoGateway

_LAT_SJ, _LON_SJ = "-31,5375", "-68,5364"


def _sucursal(
    id_: int, *, lat: str | None = _LAT_SJ, lon: str | None = _LON_SJ, domicilio: str = "Mitre 1"
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre="Empresa",
        sucursal_nombre=f"Sucursal {id_}",
        domicilio=domicilio,
        localidad="San Juan",
        provincia="San Juan",
        latitud=lat,
        longitud=lon,
    )


def _armar(clientes: list[SigesSucursalCliente], base_id: int | None = None):  # type: ignore[no-untyped-def]
    prestador = make_prestador(siges_empresa_id=504, siges_base_sucursal_id=base_id)
    propias = [
        SigesSucursalPropia(
            siges_sucursal_id=base_id, descripcion="Base", latitud=_LAT_SJ, longitud=_LON_SJ
        )
    ] if base_id is not None else []
    ports = GeovalidacionTier0Ports(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=clientes, propias=propias),
    )
    return EvaluarTier0Geovalidacion(ports), prestador.id


class TestEvaluarTier0Geovalidacion:
    @pytest.mark.asyncio
    async def test_sin_hallazgos(self) -> None:
        use_case, pid = _armar([_sucursal(1)])
        assert await use_case.execute(pid) == []

    @pytest.mark.asyncio
    async def test_sin_coordenadas_enriquecido_con_datos_de_sucursal(self) -> None:
        use_case, pid = _armar([_sucursal(1, lat=None, lon=None)])
        hallazgos = await use_case.execute(pid)
        assert len(hallazgos) == 1
        h = hallazgos[0]
        assert h.codigo == "sin_coordenadas"
        assert h.empresa_nombre == "Empresa"
        assert h.sucursal_nombre == "Sucursal 1"
        assert h.latitud is None

    @pytest.mark.asyncio
    async def test_ordena_por_severidad_alta_primero(self) -> None:
        clientes = [
            _sucursal(1),  # limpia
            _sucursal(2, lat=None, lon=None),  # baja
            _sucursal(3, lat="1", lon="1"),  # fuera de argentina -> alta
        ]
        use_case, pid = _armar(clientes)
        hallazgos = await use_case.execute(pid)
        assert [h.severidad for h in hallazgos] == ["alta", "baja"]

    @pytest.mark.asyncio
    async def test_evalua_distancia_a_base_configurada(self) -> None:
        lejos = _sucursal(1, lat="-38,0", lon="-57,5")  # ~700 km de San Juan
        use_case, pid = _armar([lejos], base_id=uuid.uuid4().int % 100000)
        hallazgos = await use_case.execute(pid)
        assert any(h.codigo == "lejos_de_base" for h in hallazgos)

    @pytest.mark.asyncio
    async def test_sin_base_configurada_no_evalua_distancia(self) -> None:
        lejos = _sucursal(1, lat="-38,0", lon="-57,5")
        use_case, pid = _armar([lejos], base_id=None)
        hallazgos = await use_case.execute(pid)
        assert all(h.codigo != "lejos_de_base" for h in hallazgos)

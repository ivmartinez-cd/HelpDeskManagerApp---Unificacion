"""ConsultarGeorefReversePendientes / ListarHallazgosTier1: reverse geocoding
de Georef comparado contra la provincia declarada en Siges."""

import pytest

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    ConsultarGeorefReversePendientes,
    GeovalidacionTier1Ports,
    ListarHallazgosTier1,
)
from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeoreferenciacionGateway,
    FakeGeorefReverseCacheRepository,
    FakeSigesGeoGateway,
)

_LAT_SJ, _LON_SJ = "-31,5375", "-68,5364"
_UBICACION_SAN_JUAN = UbicacionGeoref(
    provincia_nombre="San Juan", provincia_id="70",
    departamento_nombre="Capital", departamento_id="70028",
)


def _sucursal(
    id_: int, *, lat: str | None = _LAT_SJ, lon: str | None = _LON_SJ, provincia: str = "San Juan"
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre="Empresa",
        sucursal_nombre=f"Sucursal {id_}",
        domicilio="Mitre 1",
        localidad="San Juan",
        provincia=provincia,
        latitud=lat,
        longitud=lon,
    )


async def _consultar(ports, pid, tope=10):  # type: ignore[no-untyped-def]
    return await ConsultarGeorefReversePendientes(ports, tope, pausa_segundos=0).execute(pid)


def _armar(clientes: list[SigesSucursalCliente], por_coords=None):  # type: ignore[no-untyped-def]
    prestador = make_prestador(siges_empresa_id=504)
    ports = GeovalidacionTier1Ports(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=clientes),
        georef=FakeGeoreferenciacionGateway(por_coords or {}),
        georef_cache=FakeGeorefReverseCacheRepository(),
    )
    return ports, prestador.id


class TestConsultarGeorefReversePendientes:
    @pytest.mark.asyncio
    async def test_consulta_y_cachea(self) -> None:
        coords = (-31.5375, -68.5364)
        ports, pid = _armar([_sucursal(1)], {coords: _UBICACION_SAN_JUAN})

        resultado = await _consultar(ports, pid)

        assert resultado.consultadas == 1
        assert ports.georef.llamadas == [coords]  # type: ignore[attr-defined]
        cacheado = await ports.georef_cache.get(*coords)
        assert cacheado is not None and cacheado.ubicacion == _UBICACION_SAN_JUAN

    @pytest.mark.asyncio
    async def test_ya_cacheada_no_vuelve_a_consultar(self) -> None:
        coords = (-31.5375, -68.5364)
        ports, pid = _armar([_sucursal(1)], {coords: _UBICACION_SAN_JUAN})
        await ports.georef_cache.put(*coords, _UBICACION_SAN_JUAN)

        resultado = await _consultar(ports, pid)

        assert resultado.consultadas == 0
        assert resultado.ya_en_cache == 1
        assert ports.georef.llamadas == []  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_sin_coordenadas_no_consulta(self) -> None:
        ports, pid = _armar([_sucursal(1, lat=None, lon=None)])

        resultado = await _consultar(ports, pid)

        assert resultado.sin_coordenadas == 1
        assert resultado.consultadas == 0

    @pytest.mark.asyncio
    async def test_respeta_el_tope(self) -> None:
        clientes = [
            _sucursal(1, lat="-31,5375", lon="-68,5364"),
            _sucursal(2, lat="-31,54", lon="-68,54"),
        ]
        ports, pid = _armar(clientes, {
            (-31.5375, -68.5364): _UBICACION_SAN_JUAN,
            (-31.54, -68.54): _UBICACION_SAN_JUAN,
        })

        resultado = await _consultar(ports, pid, tope=1)

        assert resultado.consultadas == 1
        assert resultado.pendientes_por_tope == 1


class TestListarHallazgosTier1:
    @pytest.mark.asyncio
    async def test_provincia_incompatible_genera_hallazgo(self) -> None:
        coords = (-31.5375, -68.5364)
        ports, pid = _armar([_sucursal(1, provincia="Mendoza")])
        await ports.georef_cache.put(*coords, _UBICACION_SAN_JUAN)

        hallazgos = await ListarHallazgosTier1(ports).execute(pid)

        assert len(hallazgos) == 1
        assert hallazgos[0].provincia_declarada == "Mendoza"
        assert hallazgos[0].provincia_georef == "San Juan"

    @pytest.mark.asyncio
    async def test_provincia_compatible_no_genera_hallazgo(self) -> None:
        coords = (-31.5375, -68.5364)
        ports, pid = _armar([_sucursal(1, provincia="San Juan")])
        await ports.georef_cache.put(*coords, _UBICACION_SAN_JUAN)

        assert await ListarHallazgosTier1(ports).execute(pid) == []

    @pytest.mark.asyncio
    async def test_sin_cachear_no_genera_hallazgo(self) -> None:
        ports, pid = _armar([_sucursal(1, provincia="Mendoza")])

        assert await ListarHallazgosTier1(ports).execute(pid) == []

    @pytest.mark.asyncio
    async def test_sin_cobertura_georef_no_genera_hallazgo(self) -> None:
        coords = (-31.5375, -68.5364)
        ports, pid = _armar([_sucursal(1, provincia="Mendoza")])
        await ports.georef_cache.put(*coords, None)

        assert await ListarHallazgosTier1(ports).execute(pid) == []

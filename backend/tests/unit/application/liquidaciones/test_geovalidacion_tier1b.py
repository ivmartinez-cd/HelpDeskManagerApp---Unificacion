"""ConsultarNominatimPendientes / ListarHallazgosTier1b: segunda opinión de
Nominatim, solo sobre lo que Georef ya marcó incompatible."""

import pytest

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    GeovalidacionTier1Ports,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    ConsultarNominatimPendientes,
    GeovalidacionTier1bPorts,
    ListarHallazgosTier1b,
)
from src.modules.liquidaciones.domain.repositories.georeferenciacion_gateway import (
    UbicacionGeoref,
)
from src.modules.liquidaciones.domain.repositories.nominatim_gateway import UbicacionNominatim
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeoreferenciacionGateway,
    FakeGeorefReverseCacheRepository,
    FakeNominatimGateway,
    FakeNominatimReverseCacheRepository,
    FakeSigesGeoGateway,
)

_COORDS = (-31.5375, -68.5364)
_UBICACION_LA_PAMPA = UbicacionGeoref(
    provincia_nombre="La Pampa", provincia_id="42", departamento_nombre=None, departamento_id=None
)


def _sucursal(id_: int, *, provincia: str = "San Juan") -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre="Empresa",
        sucursal_nombre=f"Sucursal {id_}",
        domicilio="Mitre 1",
        localidad="San Juan",
        provincia=provincia,
        latitud="-31,5375",
        longitud="-68,5364",
    )


def _armar(clientes, nominatim_por_coords=None, georef_confirma_incompatible=True):  # type: ignore[no-untyped-def]
    prestador = make_prestador(siges_empresa_id=504)
    georef_cache = FakeGeorefReverseCacheRepository()
    tier1_ports = GeovalidacionTier1Ports(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=clientes),
        georef=FakeGeoreferenciacionGateway(),
        georef_cache=georef_cache,
    )
    ports = GeovalidacionTier1bPorts(
        tier1=tier1_ports,
        nominatim=FakeNominatimGateway(nominatim_por_coords or {}),
        nominatim_cache=FakeNominatimReverseCacheRepository(),
    )
    return ports, georef_cache, prestador.id


class TestConsultarNominatimPendientes:
    @pytest.mark.asyncio
    async def test_consulta_solo_lo_que_georef_marco_incompatible(self) -> None:
        ports, georef_cache, pid = _armar(
            [_sucursal(1, provincia="Mendoza")], {_COORDS: UbicacionNominatim("La Pampa")}
        )
        await georef_cache.put(*_COORDS, _UBICACION_LA_PAMPA)

        resultado = await ConsultarNominatimPendientes(ports, tope=10).execute(pid)

        assert resultado.consultadas == 1
        assert ports.nominatim.llamadas == [_COORDS]  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_no_consulta_lo_que_georef_ya_confirmo_compatible(self) -> None:
        ports, georef_cache, pid = _armar([_sucursal(1, provincia="San Juan")])
        ubicacion_compatible = UbicacionGeoref(
            provincia_nombre="San Juan", provincia_id="70",
            departamento_nombre=None, departamento_id=None,
        )
        await georef_cache.put(*_COORDS, ubicacion_compatible)

        resultado = await ConsultarNominatimPendientes(ports, tope=10).execute(pid)

        assert resultado.consultadas == 0
        assert ports.nominatim.llamadas == []  # type: ignore[attr-defined]


class TestListarHallazgosTier1b:
    @pytest.mark.asyncio
    async def test_dos_fuentes_de_acuerdo_confirma(self) -> None:
        ports, georef_cache, pid = _armar(
            [_sucursal(1, provincia="Mendoza")], {_COORDS: UbicacionNominatim("La Pampa")}
        )
        await georef_cache.put(*_COORDS, _UBICACION_LA_PAMPA)
        await ports.nominatim_cache.put(*_COORDS, UbicacionNominatim("La Pampa"))

        confirmados = await ListarHallazgosTier1b(ports).execute(pid)

        assert len(confirmados) == 1
        assert confirmados[0].provincia_georef == "La Pampa"
        assert confirmados[0].provincia_nominatim == "La Pampa"

    @pytest.mark.asyncio
    async def test_nominatim_discrepa_no_confirma(self) -> None:
        ports, georef_cache, pid = _armar([_sucursal(1, provincia="Mendoza")])
        await georef_cache.put(*_COORDS, _UBICACION_LA_PAMPA)
        await ports.nominatim_cache.put(*_COORDS, UbicacionNominatim("Chubut"))

        assert await ListarHallazgosTier1b(ports).execute(pid) == []

    @pytest.mark.asyncio
    async def test_sin_cachear_nominatim_no_confirma(self) -> None:
        ports, georef_cache, pid = _armar([_sucursal(1, provincia="Mendoza")])
        await georef_cache.put(*_COORDS, _UBICACION_LA_PAMPA)

        assert await ListarHallazgosTier1b(ports).execute(pid) == []

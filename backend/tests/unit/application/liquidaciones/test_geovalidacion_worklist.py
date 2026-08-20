"""CalcularWorklistTier2: cruza Tier0+Tier1b para el residuo real de Tier 2."""

import pytest

from src.modules.liquidaciones.application.use_cases.geovalidacion_tier0 import (
    EvaluarTier0Geovalidacion,
    GeovalidacionTier0Ports,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1 import (
    GeovalidacionTier1Ports,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_tier1b import (
    GeovalidacionTier1bPorts,
    ListarHallazgosTier1b,
)
from src.modules.liquidaciones.application.use_cases.geovalidacion_worklist import (
    CalcularWorklistTier2,
    WorklistTier2Ports,
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
    FakeGeocodeCacheRepository,
    FakeGeoreferenciacionGateway,
    FakeGeorefReverseCacheRepository,
    FakeNominatimGateway,
    FakeNominatimReverseCacheRepository,
    FakeSigesGeoGateway,
)

_LAT_SJ, _LON_SJ = "-31,5375", "-68,5364"


def _sucursal(
    id_: int, *, provincia: str = "San Juan", domicilio: str = "Mitre 1"
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_,
        empresa_nombre="Empresa",
        sucursal_nombre=f"Sucursal {id_}",
        domicilio=domicilio,
        localidad="San Juan",
        provincia=provincia,
        latitud=_LAT_SJ,
        longitud=_LON_SJ,
    )


def _armar(clientes: list[SigesSucursalCliente]):  # type: ignore[no-untyped-def]
    prestador = make_prestador(siges_empresa_id=504)
    siges = FakeSigesGeoGateway(clientes=clientes)
    prestadores = FakePrestadorRepository({prestador.id: prestador})
    tier0_ports = GeovalidacionTier0Ports(prestadores=prestadores, siges=siges)
    tier1_ports = GeovalidacionTier1Ports(
        prestadores=prestadores, siges=siges,
        georef=FakeGeoreferenciacionGateway(), georef_cache=FakeGeorefReverseCacheRepository(),
    )
    tier1b_ports = GeovalidacionTier1bPorts(
        tier1=tier1_ports, nominatim=FakeNominatimGateway(),
        nominatim_cache=FakeNominatimReverseCacheRepository(),
    )
    geocode_cache = FakeGeocodeCacheRepository()
    ports = WorklistTier2Ports(
        prestadores=prestadores,
        siges=siges,
        geocode_cache=geocode_cache,
        evaluar_tier0=EvaluarTier0Geovalidacion(tier0_ports),
        listar_tier1b=ListarHallazgosTier1b(tier1b_ports),
    )
    return ports, geocode_cache, tier1b_ports, prestador.id


class TestCalcularWorklistTier2:
    @pytest.mark.asyncio
    async def test_sin_hallazgos_no_hay_residuo(self) -> None:
        ports, _, _, pid = _armar([_sucursal(1)])
        resultado = await CalcularWorklistTier2(ports).execute(pid)
        assert resultado.certeza_absoluta == []
        assert resultado.requiere_verificacion == []
        assert resultado.estimacion_llamadas_google == 0

    @pytest.mark.asyncio
    async def test_pin_compartido_sin_confirmar_va_a_verificacion(self) -> None:
        clientes = [
            _sucursal(1, domicilio="Mitre 100"),
            _sucursal(2, domicilio="Rivadavia 200"),
        ]
        ports, _, _, pid = _armar(clientes)

        resultado = await CalcularWorklistTier2(ports).execute(pid)

        ids = {i.siges_sucursal_id for i in resultado.requiere_verificacion}
        assert ids == {1, 2}
        assert resultado.estimacion_llamadas_google == 2  # ninguna en geocode_cache todavia

    @pytest.mark.asyncio
    async def test_confirmado_por_tier1b_no_entra_al_residuo(self) -> None:
        clientes = [
            _sucursal(1, provincia="Mendoza", domicilio="Mitre 100"),
            _sucursal(2, provincia="Mendoza", domicilio="Rivadavia 200"),
        ]
        ports, _, tier1b_ports, pid = _armar(clientes)
        ubicacion = UbicacionGeoref(
            provincia_nombre="San Juan", provincia_id="70",
            departamento_nombre=None, departamento_id=None,
        )
        await tier1b_ports.tier1.georef_cache.put(-31.5375, -68.5364, ubicacion)
        await tier1b_ports.nominatim_cache.put(-31.5375, -68.5364, UbicacionNominatim("San Juan"))

        resultado = await CalcularWorklistTier2(ports).execute(pid)

        assert resultado.requiere_verificacion == []

    @pytest.mark.asyncio
    async def test_estimacion_descuenta_lo_ya_cacheado_en_google(self) -> None:
        clientes = [
            _sucursal(1, domicilio="Mitre 100"),
            _sucursal(2, domicilio="Rivadavia 200"),
        ]
        ports, geocode_cache, _, pid = _armar(clientes)
        direccion_1 = "Mitre 100, San Juan, San Juan, Argentina"
        await geocode_cache.put(direccion_1, [])

        resultado = await CalcularWorklistTier2(ports).execute(pid)

        assert resultado.estimacion_llamadas_google == 1

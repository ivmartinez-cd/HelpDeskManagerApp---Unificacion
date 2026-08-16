"""GeocodificarSucursales: llena vacíos con cache y tope, auto-resuelve solo
inequívocos, nunca toca sucursales con pin en Siges ni resoluciones previas."""

from uuid import UUID

import pytest

from src.modules.liquidaciones.application.use_cases.geocodificar_sucursales import (
    GeocodificarPorts,
    GeocodificarSucursales,
)
from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeocodeCacheRepository,
    FakeGeocodingGateway,
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
)

_DIRECCION = "Avenida Callao 1337, CABA, Capital Federal, Argentina"
_ROOFTOP = GeocodeCandidato(
    formatted_address="Av. Callao 1337, C1023AAG CABA, Argentina",
    latitud=-34.593456,
    longitud=-58.392671,
    location_type="ROOFTOP",
    tipos=("street_address",),
)
_RUTA = GeocodeCandidato(
    formatted_address="RN33, Argentina",
    latitud=-36.0252331,
    longitud=-62.7410169,
    location_type="GEOMETRIC_CENTER",
    tipos=("route",),
)


def _sucursal(
    siges_id: int = 1,
    domicilio: str | None = "Avenida Callao 1337 Piso: Dpto:",
    localidad: str | None = "CABA",
    provincia: str | None = "Capital Federal",
    latitud: str | None = None,
    longitud: str | None = None,
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre="Dia %",
        sucursal_nombre=f"Tienda {siges_id}",
        domicilio=domicilio,
        localidad=localidad,
        provincia=provincia,
        latitud=latitud,
        longitud=longitud,
    )


def _armar(
    sucursales: list[SigesSucursalCliente],
    geocoding: FakeGeocodingGateway,
    tope: int = 200,
) -> tuple[GeocodificarSucursales, GeocodificarPorts, UUID]:
    prestador = make_prestador(siges_empresa_id=77, siges_base_sucursal_id=9)
    ports = GeocodificarPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=sucursales),
        sucursal_coords=FakeSucursalCoordenadasRepository(),
        geocode_cache=FakeGeocodeCacheRepository(),
        geocoding=geocoding,
    )
    return GeocodificarSucursales(ports, tope), ports, prestador.id


class TestGeocodificarSucursales:
    @pytest.mark.asyncio
    async def test_auto_resuelve_candidato_inequivoco(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_ROOFTOP]})
        use_case, ports, prestador_id = _armar([_sucursal()], geocoding)
        resultado = await use_case.execute(prestador_id)
        assert resultado.resueltas_auto == 1
        assert resultado.llamadas_google == 1
        fila = await ports.sucursal_coords.get_by_siges_sucursal_id(1)
        assert fila is not None and fila.resuelta
        assert fila.procedencia == "geocode"
        assert fila.latitud == _ROOFTOP.latitud

    @pytest.mark.asyncio
    async def test_segunda_corrida_no_llama_a_google(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_ROOFTOP]})
        use_case, _, prestador_id = _armar([_sucursal()], geocoding)
        await use_case.execute(prestador_id)
        resultado = await use_case.execute(prestador_id)
        assert resultado.ya_resueltas == 1
        assert resultado.llamadas_google == 0
        assert len(geocoding.llamadas) == 1

    @pytest.mark.asyncio
    async def test_centro_de_ruta_queda_ambiguo(self) -> None:
        direccion = "Ruta Nacional 33 KM 167, GUAMINI, Buenos Aires, Argentina"
        geocoding = FakeGeocodingGateway({direccion: [_RUTA]})
        sucursal = _sucursal(
            domicilio="Ruta Nacional 33 KM 167", localidad="GUAMINI", provincia="Buenos Aires"
        )
        use_case, ports, prestador_id = _armar([sucursal], geocoding)
        resultado = await use_case.execute(prestador_id)
        assert resultado.ambiguas == 1
        fila = await ports.sucursal_coords.get_by_siges_sucursal_id(1)
        assert fila is not None and not fila.resuelta

    @pytest.mark.asyncio
    async def test_con_pin_en_siges_no_se_toca(self) -> None:
        geocoding = FakeGeocodingGateway()
        sucursal = _sucursal(latitud="-34,5", longitud="-58,4")
        use_case, ports, prestador_id = _armar([sucursal], geocoding)
        resultado = await use_case.execute(prestador_id)
        assert resultado.llamadas_google == 0
        assert await ports.sucursal_coords.get_by_siges_sucursal_id(1) is None

    @pytest.mark.asyncio
    async def test_sin_direccion(self) -> None:
        use_case, _, prestador_id = _armar(
            [_sucursal(domicilio=None, localidad=None)], FakeGeocodingGateway()
        )
        resultado = await use_case.execute(prestador_id)
        assert resultado.sin_direccion == 1
        assert resultado.llamadas_google == 0

    @pytest.mark.asyncio
    async def test_zero_results_se_cachea(self) -> None:
        geocoding = FakeGeocodingGateway({})
        use_case, _, prestador_id = _armar([_sucursal()], geocoding)
        await use_case.execute(prestador_id)
        resultado = await use_case.execute(prestador_id)
        assert resultado.sin_resultados == 1
        assert len(geocoding.llamadas) == 1

    @pytest.mark.asyncio
    async def test_tope_corta_la_corrida(self) -> None:
        d1 = "Calle Uno 1, CABA, Capital Federal, Argentina"
        d2 = "Calle Dos 2, CABA, Capital Federal, Argentina"
        geocoding = FakeGeocodingGateway({d1: [_ROOFTOP], d2: [_ROOFTOP]})
        sucursales = [
            _sucursal(siges_id=1, domicilio="Calle Uno 1"),
            _sucursal(siges_id=2, domicilio="Calle Dos 2"),
        ]
        use_case, _, prestador_id = _armar(sucursales, geocoding, tope=1)
        resultado = await use_case.execute(prestador_id)
        assert resultado.llamadas_google == 1
        assert resultado.pendientes_por_tope == 1

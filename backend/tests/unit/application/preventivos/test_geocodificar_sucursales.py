from datetime import UTC, datetime

from src.modules.preventivos.application.use_cases.geocodificar_sucursales import (
    GeocodificarSucursalesDependencies,
    GeocodificarSucursalesUseCase,
)
from src.modules.preventivos.domain.entities.sucursal_coordenadas import SucursalCoordenadas
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato
from tests.unit.application.preventivos.fakes import (
    FakeGeocodeCacheRepository,
    FakeGeocodingGateway,
    FakePreventivosQueryGateway,
    FakeSucursalCoordenadasRepository,
    build_sucursal_geocoding,
)

_CANDIDATO_PRECISO = GeocodeCandidato(
    formatted_address="Av. Siempre Viva 742, Springfield",
    latitud=-31.5,
    longitud=-68.5,
    location_type="ROOFTOP",
    tipos=(),
    partial_match=False,
)


def _use_case(
    sucursales,
    *,
    por_direccion: dict[str, list[GeocodeCandidato]] | None = None,
    coordenadas: FakeSucursalCoordenadasRepository | None = None,
    tope: int = 200,
) -> tuple[GeocodificarSucursalesUseCase, FakeSucursalCoordenadasRepository, FakeGeocodingGateway]:
    gateway = FakePreventivosQueryGateway(sucursales_geocoding=sucursales)
    coords = coordenadas or FakeSucursalCoordenadasRepository()
    geocoding = FakeGeocodingGateway(por_direccion)
    use_case = GeocodificarSucursalesUseCase(
        GeocodificarSucursalesDependencies(
            query_gateway=gateway,
            sucursal_coordenadas=coords,
            geocode_cache=FakeGeocodeCacheRepository(),
            geocoding=geocoding,
        ),
        tope,
    )
    return use_case, coords, geocoding


async def test_sucursal_con_coordenada_valida_no_se_toca() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=-34.6, longitud=-58.4)]
    use_case, coords, geocoding = _use_case(sucursales)

    resultado = await use_case.execute()

    assert resultado.resueltas == 0
    assert geocoding.llamadas == []
    assert coords.resueltas == {}


async def test_sucursal_ya_resuelta_no_se_reconsulta() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=0.0, longitud=0.0, domicilio="Calle 1")]
    ya_resuelta = SucursalCoordenadas(1, -31.5, -68.5, "Calle 1, Argentina", datetime.now(UTC))
    coords = FakeSucursalCoordenadasRepository([ya_resuelta])
    use_case, _, geocoding = _use_case(sucursales, coordenadas=coords)

    resultado = await use_case.execute()

    assert resultado.resueltas == 0
    assert geocoding.llamadas == []


async def test_candidato_unico_preciso_se_resuelve_automatico() -> None:
    sucursales = [
        build_sucursal_geocoding(
            1, latitud=0.0, longitud=0.0, domicilio="San Isidro 2200", ciudad="Mendoza"
        )
    ]
    direccion = "San Isidro 2200, Mendoza, Provincia, Argentina"
    use_case, coords, _ = _use_case(sucursales, por_direccion={direccion: [_CANDIDATO_PRECISO]})

    resultado = await use_case.execute()

    assert resultado.resueltas == 1
    assert coords.resueltas[1].latitud == -31.5


async def test_sin_domicilio_no_llama_a_google() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=0.0, longitud=0.0, domicilio="")]
    use_case, _, geocoding = _use_case(sucursales)

    resultado = await use_case.execute()

    assert resultado.sin_direccion == 1
    assert geocoding.llamadas == []


async def test_zero_results_cuenta_sin_resultados() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=0.0, longitud=0.0, domicilio="Nada 123")]
    use_case, coords, _ = _use_case(sucursales, por_direccion={})

    resultado = await use_case.execute()

    assert resultado.sin_resultados == 1
    assert coords.resueltas == {}


async def test_varios_candidatos_cuenta_ambiguas() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=0.0, longitud=0.0, domicilio="Calle X")]
    direccion = "Calle X, Ciudad, Provincia, Argentina"
    use_case, coords, _ = _use_case(
        sucursales, por_direccion={direccion: [_CANDIDATO_PRECISO, _CANDIDATO_PRECISO]}
    )

    resultado = await use_case.execute()

    assert resultado.ambiguas == 1
    assert coords.resueltas == {}


async def test_tope_de_llamadas_corta_la_corrida() -> None:
    sucursales = [
        build_sucursal_geocoding(1, latitud=0.0, longitud=0.0, domicilio="Calle 1"),
        build_sucursal_geocoding(2, latitud=0.0, longitud=0.0, domicilio="Calle 2"),
    ]
    use_case, _, geocoding = _use_case(sucursales, tope=1)

    resultado = await use_case.execute()

    assert len(geocoding.llamadas) == 1
    assert resultado.sin_resultados == 1

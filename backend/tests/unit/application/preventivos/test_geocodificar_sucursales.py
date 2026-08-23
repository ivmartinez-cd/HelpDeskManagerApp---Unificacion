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


async def test_pin_compartido_entre_domicilios_distintos_se_geocodifica_igual() -> None:
    # Ambas coordenadas son "válidas" por bbox, pero comparten el mismo punto
    # exacto con un domicilio distinto — señal de pin genérico, no real.
    sucursales = [
        build_sucursal_geocoding(1, domicilio="Calle A 100", latitud=-34.6, longitud=-58.4),
        build_sucursal_geocoding(2, domicilio="Calle B 200", latitud=-34.6, longitud=-58.4),
    ]
    direccion_a = "Calle A 100, Ciudad, Provincia, Argentina"
    direccion_b = "Calle B 200, Ciudad, Provincia, Argentina"
    use_case, coords, geocoding = _use_case(
        sucursales,
        por_direccion={direccion_a: [_CANDIDATO_PRECISO], direccion_b: [_CANDIDATO_PRECISO]},
    )

    resultado = await use_case.execute()

    assert resultado.resueltas == 2
    assert sorted(geocoding.llamadas) == sorted([direccion_a, direccion_b])
    assert set(coords.resueltas) == {1, 2}


async def test_mismo_domicilio_con_pines_en_conflicto_se_geocodifica_igual() -> None:
    # Ambas coordenadas son "válidas" por bbox, pero el mismo domicilio real
    # tiene dos pines que no coinciden entre sí (caso Constituyentes).
    sucursales = [
        build_sucursal_geocoding(
            1, domicilio="Av. Constituyentes 6020", latitud=-34.5726, longitud=-58.5060
        ),
        build_sucursal_geocoding(
            2, domicilio="Av. Constituyentes 6020", latitud=-34.5623, longitud=-58.5158
        ),
    ]
    direccion = "Av. Constituyentes 6020, Ciudad, Provincia, Argentina"
    use_case, coords, geocoding = _use_case(
        sucursales, por_direccion={direccion: [_CANDIDATO_PRECISO]}
    )

    resultado = await use_case.execute()

    assert resultado.resueltas == 2
    assert geocoding.llamadas == [direccion]  # misma dirección: un solo llamado, cacheado
    assert set(coords.resueltas) == {1, 2}


async def test_mismo_domicilio_repetido_no_se_toma_como_pin_compartido() -> None:
    # Dos sucursales con la MISMA dirección real y el mismo pin: legítimo,
    # no debe disparar geocodificación.
    sucursales = [
        build_sucursal_geocoding(1, domicilio="Calle A 100", latitud=-34.6, longitud=-58.4),
        build_sucursal_geocoding(2, domicilio="Calle A 100", latitud=-34.6, longitud=-58.4),
    ]
    use_case, coords, geocoding = _use_case(sucursales)

    resultado = await use_case.execute()

    assert resultado.resueltas == 0
    assert geocoding.llamadas == []
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


async def test_siges_corregido_cerca_del_override_se_reconcilia() -> None:
    # Caso real (2026-08-23): alguien corrige la coordenada directamente en
    # Siges; el override viejo (de una geocodificación anterior) la tapaba.
    sucursales = [
        build_sucursal_geocoding(1, latitud=-34.6146, longitud=-58.4196, domicilio="Calle 1")
    ]
    ya_resuelta = SucursalCoordenadas(1, -34.6145828, -58.4195644, "Calle 1", datetime.now(UTC))
    coords = FakeSucursalCoordenadasRepository([ya_resuelta])
    use_case, coords, _ = _use_case(sucursales, coordenadas=coords)

    resultado = await use_case.execute()

    assert resultado.reconciliadas == 1
    assert 1 not in coords.resueltas


async def test_siges_sigue_lejos_del_override_no_se_reconcilia() -> None:
    sucursales = [
        build_sucursal_geocoding(1, latitud=-31.5, longitud=-68.5, domicilio="Calle 1")
    ]
    ya_resuelta = SucursalCoordenadas(1, -34.6145828, -58.4195644, "Calle 1", datetime.now(UTC))
    coords = FakeSucursalCoordenadasRepository([ya_resuelta])
    use_case, coords, _ = _use_case(sucursales, coordenadas=coords)

    resultado = await use_case.execute()

    assert resultado.reconciliadas == 0
    assert 1 in coords.resueltas


async def test_sucursal_sin_override_no_se_evalua_para_reconciliar() -> None:
    sucursales = [build_sucursal_geocoding(1, latitud=-34.6, longitud=-58.4)]
    use_case, _, _ = _use_case(sucursales)

    resultado = await use_case.execute()

    assert resultado.reconciliadas == 0


async def test_grupo_en_conflicto_no_se_reconcilia_aunque_un_miembro_este_cerca() -> None:
    # Bug real (2026-08-23), caso Constituyentes: dos sucursales con el mismo
    # domicilio y pines que no coinciden entre sí. Ambas se resuelven al
    # mismo override; una de ellas tenía su propio pin de Siges a metros del
    # valor correcto (nunca estuvo tan mal, solo entró al grupo por
    # comparación con la otra) — reconciliar solo esa rompería la
    # consistencia del grupo, que sigue en conflicto.
    sucursales = [
        build_sucursal_geocoding(
            1, domicilio="Av. Constituyentes 6020", latitud=-34.5726, longitud=-58.5077
        ),
        build_sucursal_geocoding(
            2, domicilio="Av. Constituyentes 6020", latitud=-34.5623, longitud=-58.5158
        ),
    ]
    coords = FakeSucursalCoordenadasRepository(
        [
            SucursalCoordenadas(1, -34.5724459, -58.5077299, "Constituyentes", datetime.now(UTC)),
            SucursalCoordenadas(2, -34.5724459, -58.5077299, "Constituyentes", datetime.now(UTC)),
        ]
    )
    use_case, coords, _ = _use_case(sucursales, coordenadas=coords)

    resultado = await use_case.execute()

    assert resultado.reconciliadas == 0
    assert {1, 2} <= set(coords.resueltas)

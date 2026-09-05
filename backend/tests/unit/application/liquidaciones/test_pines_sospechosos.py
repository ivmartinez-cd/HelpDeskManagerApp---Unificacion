"""Auditoría de pines: AuditarPines es cache-first y respeta el tope de
llamadas pagas; ListarPinesSospechosos solo cruza datos cacheados (nunca llama
a Google) con el umbral de 5 km; CorregirPin exige geocode cacheado y guarda
el override con procedencia geocode."""

from uuid import UUID

import pytest

from src.modules.liquidaciones.application.use_cases.pines_sospechosos import (
    AuditarPines,
    CorregirPin,
    ListarPinesSospechosos,
    PinesPorts,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from src.modules.liquidaciones.domain.services.geolocalizacion import PROCEDENCIA_GEOCODE
from src.shared.domain.errors import ValidationError
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeocodeCacheRepository,
    FakeGeocodingGateway,
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
)

_DIRECCION = "Avenida Callao 1337, CABA, Capital Federal, Argentina"
# ~11 km al sur del pin (-34,5 / -58,4): discrepancia sobre el umbral de 5 km.
_LEJOS = GeocodeCandidato(
    formatted_address="Av. Callao 1337, C1023AAG CABA, Argentina",
    latitud=-34.6,
    longitud=-58.4,
    location_type="ROOFTOP",
    tipos=("street_address",),
)
# ~1 km del pin: bajo el umbral, no es sospechoso.
_CERCA = GeocodeCandidato(
    formatted_address="Av. Callao 1300, CABA, Argentina",
    latitud=-34.509,
    longitud=-58.4,
    location_type="ROOFTOP",
    tipos=("street_address",),
)


def _sucursal(
    siges_id: int = 1,
    domicilio: str | None = "Avenida Callao 1337 Piso: Dpto:",
    latitud: str | None = "-34,5",
    longitud: str | None = "-58,4",
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre="Dia %",
        sucursal_nombre=f"Tienda {siges_id}",
        domicilio=domicilio,
        localidad="CABA",
        provincia="Capital Federal",
        latitud=latitud,
        longitud=longitud,
    )


def _armar(
    sucursales: list[SigesSucursalCliente],
    geocoding: FakeGeocodingGateway | None = None,
) -> tuple[PinesPorts, UUID]:
    prestador = make_prestador(siges_empresa_id=77, siges_base_sucursal_id=9)
    ports = PinesPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=sucursales),
        geocode_cache=FakeGeocodeCacheRepository(),
        geocoding=geocoding or FakeGeocodingGateway(),
        sucursal_coords=FakeSucursalCoordenadasRepository(),
    )
    return ports, prestador.id


class TestAuditarPines:
    @pytest.mark.asyncio
    async def test_geocodifica_solo_lo_que_no_esta_en_cache(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_LEJOS]})
        ports, prestador_id = _armar([_sucursal()], geocoding)
        resultado = await AuditarPines(ports, tope_llamadas=10).execute(prestador_id)
        assert resultado.geocodificadas == 1
        assert resultado.llamadas_google == 1
        assert await ports.geocode_cache.get(_DIRECCION) == [_LEJOS]

    @pytest.mark.asyncio
    async def test_solo_ids_acota_la_corrida_al_residuo(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_LEJOS]})
        otra_direccion = "Rivadavia 500, CABA, Capital Federal, Argentina"
        sucursales = [_sucursal(1), _sucursal(2, domicilio="Rivadavia 500")]
        ports, prestador_id = _armar(sucursales, geocoding)

        resultado = await AuditarPines(ports, tope_llamadas=10).execute(
            prestador_id, solo_ids=frozenset({1})
        )

        assert resultado.geocodificadas == 1
        assert geocoding.llamadas == [_DIRECCION]
        assert await ports.geocode_cache.get(otra_direccion) is None

    @pytest.mark.asyncio
    async def test_segunda_corrida_no_llama_a_google(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_LEJOS]})
        ports, prestador_id = _armar([_sucursal()], geocoding)
        auditar = AuditarPines(ports, tope_llamadas=10)
        await auditar.execute(prestador_id)
        resultado = await auditar.execute(prestador_id)
        assert resultado.ya_en_cache == 1
        assert resultado.llamadas_google == 0
        assert len(geocoding.llamadas) == 1

    @pytest.mark.asyncio
    async def test_tope_corta_la_corrida(self) -> None:
        sucursales = [
            _sucursal(siges_id=1, domicilio="Calle Uno 1"),
            _sucursal(siges_id=2, domicilio="Calle Dos 2"),
        ]
        ports, prestador_id = _armar(sucursales, FakeGeocodingGateway())
        resultado = await AuditarPines(ports, tope_llamadas=1).execute(prestador_id)
        assert resultado.llamadas_google == 1
        assert resultado.pendientes_por_tope == 1

    @pytest.mark.asyncio
    async def test_sin_pin_no_se_audita(self) -> None:
        geocoding = FakeGeocodingGateway()
        ports, prestador_id = _armar([_sucursal(latitud=None, longitud=None)], geocoding)
        resultado = await AuditarPines(ports, tope_llamadas=10).execute(prestador_id)
        assert resultado.llamadas_google == 0
        assert len(geocoding.llamadas) == 0

    @pytest.mark.asyncio
    async def test_con_pin_sin_direccion_se_cuenta(self) -> None:
        sin_direccion = SigesSucursalCliente(
            siges_sucursal_id=3,
            empresa_nombre="Dia %",
            sucursal_nombre="Tienda 3",
            domicilio=None,
            localidad=None,
            provincia=None,
            latitud="-34,5",
            longitud="-58,4",
        )
        ports, prestador_id = _armar([sin_direccion])
        resultado = await AuditarPines(ports, tope_llamadas=10).execute(prestador_id)
        assert resultado.sin_direccion == 1
        assert resultado.llamadas_google == 0


class TestListarPinesSospechosos:
    @pytest.mark.asyncio
    async def test_discrepancia_sobre_umbral_es_sospechoso(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        await ports.geocode_cache.put(_DIRECCION, [_LEJOS])
        pines = await ListarPinesSospechosos(ports).execute(prestador_id)
        assert len(pines) == 1
        assert pines[0].siges_sucursal_id == 1
        assert pines[0].discrepancia_km > 5
        assert pines[0].location_type == "ROOFTOP"

    @pytest.mark.asyncio
    async def test_pin_ya_corregido_desaparece_del_listado(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        await ports.geocode_cache.put(_DIRECCION, [_LEJOS])
        assert len(await ListarPinesSospechosos(ports).execute(prestador_id)) == 1

        await CorregirPin(ports).execute(prestador_id, 1)

        assert await ListarPinesSospechosos(ports).execute(prestador_id) == []

    @pytest.mark.asyncio
    async def test_discrepancia_bajo_umbral_no_es_sospechoso(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        await ports.geocode_cache.put(_DIRECCION, [_CERCA])
        assert await ListarPinesSospechosos(ports).execute(prestador_id) == []

    @pytest.mark.asyncio
    async def test_sin_cache_no_llama_a_google(self) -> None:
        geocoding = FakeGeocodingGateway({_DIRECCION: [_LEJOS]})
        ports, prestador_id = _armar([_sucursal()], geocoding)
        assert await ListarPinesSospechosos(ports).execute(prestador_id) == []
        assert len(geocoding.llamadas) == 0

    @pytest.mark.asyncio
    async def test_ordena_por_discrepancia_descendente(self) -> None:
        d2 = "Calle Dos 2, CABA, Capital Federal, Argentina"
        muy_lejos = GeocodeCandidato(
            formatted_address="Otro lado",
            latitud=-35.5,
            longitud=-58.4,
            location_type="ROOFTOP",
            tipos=("street_address",),
        )
        ports, prestador_id = _armar(
            [_sucursal(siges_id=1), _sucursal(siges_id=2, domicilio="Calle Dos 2")]
        )
        await ports.geocode_cache.put(_DIRECCION, [_LEJOS])
        await ports.geocode_cache.put(d2, [muy_lejos])
        pines = await ListarPinesSospechosos(ports).execute(prestador_id)
        assert [p.siges_sucursal_id for p in pines] == [2, 1]


class TestCorregirPin:
    @pytest.mark.asyncio
    async def test_guarda_override_con_procedencia_geocode(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        await ports.geocode_cache.put(_DIRECCION, [_LEJOS])
        await CorregirPin(ports).execute(prestador_id, siges_sucursal_id=1)
        fila = await ports.sucursal_coords.get_by_siges_sucursal_id(1)
        assert fila is not None
        assert fila.prestador_id == prestador_id
        assert fila.procedencia == PROCEDENCIA_GEOCODE
        assert fila.latitud == _LEJOS.latitud
        assert fila.formatted_address == _LEJOS.formatted_address

    @pytest.mark.asyncio
    async def test_sin_geocode_cacheado_falla(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        with pytest.raises(ValidationError):
            await CorregirPin(ports).execute(prestador_id, siges_sucursal_id=1)

    @pytest.mark.asyncio
    async def test_sucursal_inexistente_falla(self) -> None:
        ports, prestador_id = _armar([_sucursal()])
        with pytest.raises(ValidationError):
            await CorregirPin(ports).execute(prestador_id, siges_sucursal_id=999)

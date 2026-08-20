"""GenerarWorklistCsv: junta certeza absoluta (Tier0) + confirmados (Tier1b)
+ pines sospechosos (Tier2/Google) en filas listas para exportar a CSV."""

import pytest

from src.modules.liquidaciones.application.use_cases.geovalidacion_csv import (
    GenerarWorklistCsv,
    WorklistCsvPorts,
)
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
from src.modules.liquidaciones.application.use_cases.pines_sospechosos import (
    ListarPinesSospechosos,
    PinesPorts,
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
    FakeGeoreferenciacionGateway,
    FakeGeorefReverseCacheRepository,
    FakeNominatimGateway,
    FakeNominatimReverseCacheRepository,
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
)


def _sucursal(id_: int, *, lat: str | None = "1", lon: str | None = "1") -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=id_, empresa_nombre="Empresa", sucursal_nombre=f"Sucursal {id_}",
        domicilio="Mitre 1", localidad="San Juan", provincia="San Juan", latitud=lat, longitud=lon,
    )


def _armar(clientes: list[SigesSucursalCliente]):  # type: ignore[no-untyped-def]
    prestador = make_prestador(siges_empresa_id=504)
    prestadores = FakePrestadorRepository({prestador.id: prestador})
    siges = FakeSigesGeoGateway(clientes=clientes)
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
    worklist_ports = WorklistTier2Ports(
        prestadores=prestadores, siges=siges, geocode_cache=geocode_cache,
        evaluar_tier0=EvaluarTier0Geovalidacion(tier0_ports),
        listar_tier1b=ListarHallazgosTier1b(tier1b_ports),
    )
    pines_ports = PinesPorts(
        prestadores=prestadores, siges=siges, geocode_cache=geocode_cache,
        geocoding=FakeGeocodingGateway(), sucursal_coords=FakeSucursalCoordenadasRepository(),
    )
    ports = WorklistCsvPorts(
        calcular_worklist=CalcularWorklistTier2(worklist_ports),
        listar_tier1b=ListarHallazgosTier1b(tier1b_ports),
        listar_pines=ListarPinesSospechosos(pines_ports),
    )
    return ports, geocode_cache, prestador.id


class TestGenerarWorklistCsv:
    @pytest.mark.asyncio
    async def test_certeza_absoluta_latlon_invertidas_sugiere_el_swap(self) -> None:
        # lat=1,lon=1 dentro de bbox no dispara nada; forzamos con coords que
        # SI activan latlon_invertidas: fuera de argentina pero invertido cae dentro.
        ports, _, pid = _armar([_sucursal(1, lat="-68,5364", lon="-31,5375")])

        filas = await GenerarWorklistCsv(ports).execute(pid)

        tier0 = [f for f in filas if f.tier == "0"]
        assert len(tier0) == 1
        assert tier0[0].latitud_sugerida == -31.5375
        assert tier0[0].longitud_sugerida == -68.5364

    @pytest.mark.asyncio
    async def test_pin_sospechoso_tier2_incluye_pin_sugerido_de_google(self) -> None:
        candidato = GeocodeCandidato(
            formatted_address="Mitre 1, San Juan", latitud=-40.0, longitud=-70.0,
            location_type="ROOFTOP", tipos=("street_address",),
        )
        ports, geocode_cache, pid = _armar([_sucursal(1, lat="-31,5375", lon="-68,5364")])
        await geocode_cache.put("Mitre 1, San Juan, San Juan, Argentina", [candidato])

        filas = await GenerarWorklistCsv(ports).execute(pid)

        tier2 = [f for f in filas if f.tier == "2"]
        assert len(tier2) == 1
        assert tier2[0].latitud_sugerida == -40.0
        assert tier2[0].longitud_sugerida == -70.0
        assert "km de discrepancia" in tier2[0].evidencia

    @pytest.mark.asyncio
    async def test_sin_hallazgos_lista_vacia(self) -> None:
        ports, _, pid = _armar([_sucursal(1, lat="-31,5375", lon="-68,5364")])
        assert await GenerarWorklistCsv(ports).execute(pid) == []

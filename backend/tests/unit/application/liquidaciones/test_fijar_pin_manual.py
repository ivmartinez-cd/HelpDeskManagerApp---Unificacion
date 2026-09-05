"""FijarPinManual: coordenadas con evidencia para una sucursal de Siges, tenga o no pin."""

import pytest

from src.modules.liquidaciones.application.use_cases.fijar_pin_manual import (
    FijarPinManual,
    FijarPinManualPorts,
)
from src.modules.liquidaciones.domain.errors import PinManualInvalidoError
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeSigesGeoGateway,
    FakeSucursalCoordenadasRepository,
)


def _armar(sucursales: list[SigesSucursalCliente]):
    prestador = make_prestador(siges_empresa_id=77, siges_base_sucursal_id=9)
    ports = FijarPinManualPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        siges=FakeSigesGeoGateway(clientes=sucursales),
        sucursal_coords=FakeSucursalCoordenadasRepository(),
    )
    return FijarPinManual(ports), ports, prestador.id


def _sucursal(siges_id: int = 1) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre="Dia %",
        sucursal_nombre="Tienda 1",
        domicilio="Alsina 100",
        localidad="Bahía Blanca",
        provincia="Buenos Aires",
        latitud="36.778",
        longitud="-119.417",
    )


@pytest.mark.asyncio
async def test_crea_override_manual_con_fuente_aunque_tenga_pin_roto() -> None:
    use_case, ports, prestador_id = _armar([_sucursal()])

    resuelta = await use_case.execute(
        prestador_id, 1, latitud=-38.7183, longitud=-62.2663, fuente="https://osm.org/x"
    )

    assert resuelta.resuelta
    assert resuelta.procedencia == "manual"
    assert resuelta.formatted_address == "https://osm.org/x"
    fila = await ports.sucursal_coords.get_by_siges_sucursal_id(1)
    assert fila is not None and fila.latitud == -38.7183


@pytest.mark.asyncio
async def test_coordenadas_fuera_de_argentina_rechazadas() -> None:
    use_case, _, prestador_id = _armar([_sucursal()])
    with pytest.raises(PinManualInvalidoError):
        await use_case.execute(prestador_id, 1, latitud=36.778, longitud=-119.417, fuente="x")


@pytest.mark.asyncio
async def test_sucursal_ajena_rechazada() -> None:
    use_case, _, prestador_id = _armar([_sucursal(1)])
    with pytest.raises(PinManualInvalidoError):
        await use_case.execute(prestador_id, 99, latitud=-38.7, longitud=-62.2, fuente="x")


@pytest.mark.asyncio
async def test_sin_fuente_rechazado() -> None:
    use_case, _, prestador_id = _armar([_sucursal()])
    with pytest.raises(PinManualInvalidoError):
        await use_case.execute(prestador_id, 1, latitud=-38.7, longitud=-62.2, fuente="  ")

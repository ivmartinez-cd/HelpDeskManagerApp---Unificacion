"""ConfirmarVinculoTablaKm / RechazarPropuestaTablaKm: decisión humana sobre
un candidato N2 de matching de sucursales."""

import uuid
from datetime import datetime

import pytest

from src.modules.liquidaciones.application.use_cases.matching_confirmar_rechazar_tabla_km import (
    ConfirmarRechazarPorts,
    ConfirmarVinculoTablaKm,
    RechazarPropuestaTablaKm,
    SigesSucursalNoEncontradaError,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.errors import TablaKmNoEncontradaError
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeMatchingDescarteRepository,
    FakeSigesGeoGateway,
    FakeTablaKmGeoRepository,
)

_AHORA = datetime(2026, 1, 1)


def _armar(siges: list[SigesSucursalCliente]):  # type: ignore[no-untyped-def]
    prestador_id = uuid.uuid4()
    prestador = make_prestador(id=prestador_id, siges_empresa_id=504, siges_base_sucursal_id=9)
    fila = TablaKm(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre="Gobierno de San Juan",
        sucursal_nombre='Escuela Marcos Sastre "Emer"',
        observaciones=None,
        domicilio_cliente=None,
        localidad_cliente=None,
        provincia_cliente=None,
        kms_recorrido=0.0,
        umbral_viatico=30.0,
        aplica_viatico=False,
        kms_a_facturar=0.0,
        url_maps=None,
        created_at=_AHORA,
        updated_at=_AHORA,
    )
    tabla_km = FakeTablaKmGeoRepository([fila])
    descartes = FakeMatchingDescarteRepository()
    ports = ConfirmarRechazarPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        tabla_km=tabla_km,
        siges=FakeSigesGeoGateway(clientes=siges),
        descartes=descartes,
    )
    return ports, tabla_km, descartes, fila.id


def _siges(siges_id: int) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre="Gobierno de San Juan",
        sucursal_nombre="Escuela rural Marcos Sastre",
        domicilio="Calle Falsa 123",
        localidad="San Juan",
        provincia="San Juan",
        id_costo_servicios=5,
    )


class TestConfirmarVinculoTablaKm:
    @pytest.mark.asyncio
    async def test_confirma_y_trae_domicilio(self) -> None:
        ports, tabla_km, _, fila_id = _armar([_siges(2)])

        actualizada = await ConfirmarVinculoTablaKm(ports).execute(fila_id, 2)

        assert actualizada.siges_sucursal_id == 2
        assert actualizada.domicilio_cliente == "Calle Falsa 123"
        assert tabla_km.rows[fila_id].siges_sucursal_id == 2

    @pytest.mark.asyncio
    async def test_candidato_inexistente_falla(self) -> None:
        ports, _, _, fila_id = _armar([_siges(2)])

        with pytest.raises(SigesSucursalNoEncontradaError):
            await ConfirmarVinculoTablaKm(ports).execute(fila_id, 999)

    @pytest.mark.asyncio
    async def test_fila_inexistente_falla(self) -> None:
        ports, _, _, _ = _armar([_siges(2)])

        with pytest.raises(TablaKmNoEncontradaError):
            await ConfirmarVinculoTablaKm(ports).execute(uuid.uuid4(), 2)


class TestRechazarPropuestaTablaKm:
    @pytest.mark.asyncio
    async def test_persiste_descarte(self) -> None:
        _, _, descartes, fila_id = _armar([_siges(2)])

        await RechazarPropuestaTablaKm(descartes).execute(fila_id, 2, "operador@canaldirecto.com")

        assert await descartes.list_descartados_por_fila([fila_id]) == {fila_id: {2}}

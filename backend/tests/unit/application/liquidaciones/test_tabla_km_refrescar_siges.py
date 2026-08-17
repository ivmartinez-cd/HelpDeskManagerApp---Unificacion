"""RefrescarDatosSiges: sincroniza domicilios desde Siges y backfillea el
vínculo (siges_sucursal_id/id_costo_servicios) en filas cuyo domicilio ya
coincidía — sin tocar geocode ni dirección en ese caso."""

import dataclasses
import uuid
from datetime import datetime
from uuid import UUID

import pytest

from src.modules.liquidaciones.application.use_cases.tabla_km_lugares import (
    TablaKmLugaresPorts,
)
from src.modules.liquidaciones.application.use_cases.tabla_km_refrescar_siges import (
    RefrescarDatosSiges,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador
from tests.unit.domain.liquidaciones.fakes import FakePrestadorRepository
from tests.unit.domain.liquidaciones.fakes_geolocalizacion import (
    FakeGeocodeCacheRepository,
    FakeGeocodingGateway,
    FakeSigesGeoGateway,
    FakeTablaKmGeoRepository,
)

_AHORA = datetime(2026, 1, 1)


def _fila(
    prestador_id: UUID,
    *,
    empresa: str = "Dia %",
    sucursal: str = "Tienda 1",
    domicilio: str | None = "Avenida Callao 1337",
    siges_sucursal_id: int | None = None,
    id_costo_servicios: int | None = None,
    geocode_formatted_address: str | None = "Av. Callao 1337, CABA",
) -> TablaKm:
    return TablaKm(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        observaciones="visita con llave",
        domicilio_cliente=domicilio,
        localidad_cliente="CABA",
        provincia_cliente="Capital Federal",
        kms_recorrido=12.0,
        umbral_viatico=30.0,
        aplica_viatico=False,
        kms_a_facturar=0.0,
        url_maps=None,
        created_at=_AHORA,
        updated_at=_AHORA,
        geocode_formatted_address=geocode_formatted_address,
        geocode_fecha=_AHORA,
        siges_sucursal_id=siges_sucursal_id,
        id_costo_servicios=id_costo_servicios,
    )


def _siges(
    *,
    siges_id: int = 101,
    empresa: str = "Dia %",
    sucursal: str = "Tienda 1",
    domicilio: str | None = "Avenida Callao 1337",
    id_costo_servicios: int | None = 7,
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio=domicilio,
        localidad="CABA",
        provincia="Capital Federal",
        latitud=None,
        longitud=None,
        cuadricula=None,
        id_costo_servicios=id_costo_servicios,
    )


def _armar(
    filas: list[TablaKm], sucursales_siges: list[SigesSucursalCliente]
) -> tuple[RefrescarDatosSiges, FakeTablaKmGeoRepository, UUID]:
    prestador = make_prestador(siges_empresa_id=77, siges_base_sucursal_id=9)
    filas = [dataclasses.replace(f, prestador_id=prestador.id) for f in filas]
    tabla_km = FakeTablaKmGeoRepository(filas)
    ports = TablaKmLugaresPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        tabla_km=tabla_km,
        siges=FakeSigesGeoGateway(clientes=sucursales_siges),
        geocode_cache=FakeGeocodeCacheRepository(),
        geocoding=FakeGeocodingGateway(),
        google_maps=None,  # type: ignore[arg-type]  # no se usa en este use case
    )
    return RefrescarDatosSiges(ports), tabla_km, prestador.id


class TestRefrescarDatosSiges:
    @pytest.mark.asyncio
    async def test_domicilio_cambiado_actualiza_direccion_y_vinculo(self) -> None:
        prestador_id = uuid.uuid4()
        fila = _fila(prestador_id, domicilio="Direccion vieja 1")
        use_case, tabla_km, pid = _armar([fila], [_siges()])
        resultado = await use_case.execute(pid)
        assert resultado.actualizadas == 1
        assert resultado.vinculadas == 0
        actualizada = tabla_km.rows[fila.id]
        assert actualizada.domicilio_cliente == "Avenida Callao 1337"
        assert actualizada.siges_sucursal_id == 101
        assert actualizada.id_costo_servicios == 7

    @pytest.mark.asyncio
    async def test_sin_cambio_de_domicilio_backfillea_vinculo_sin_tocar_geocode(
        self,
    ) -> None:
        prestador_id = uuid.uuid4()
        fila = _fila(prestador_id, siges_sucursal_id=None)
        use_case, tabla_km, pid = _armar([fila], [_siges()])
        resultado = await use_case.execute(pid)
        assert resultado.sin_cambios == 1
        assert resultado.vinculadas == 1
        vinculada = tabla_km.rows[fila.id]
        assert vinculada.siges_sucursal_id == 101
        assert vinculada.id_costo_servicios == 7
        # El backfill NO pasa por update_domicilio: el geocode queda intacto.
        assert vinculada.geocode_formatted_address == "Av. Callao 1337, CABA"
        assert vinculada.domicilio_cliente == "Avenida Callao 1337"

    @pytest.mark.asyncio
    async def test_vinculo_ya_correcto_es_noop(self) -> None:
        prestador_id = uuid.uuid4()
        fila = _fila(prestador_id, siges_sucursal_id=101, id_costo_servicios=7)
        use_case, tabla_km, pid = _armar([fila], [_siges()])
        antes = tabla_km.rows[fila.id]
        resultado = await use_case.execute(pid)
        assert resultado.sin_cambios == 1
        assert resultado.vinculadas == 0
        assert tabla_km.rows[fila.id] is antes

    @pytest.mark.asyncio
    async def test_cambio_de_id_costo_con_domicilio_igual_revincula(self) -> None:
        prestador_id = uuid.uuid4()
        fila = _fila(prestador_id, siges_sucursal_id=101, id_costo_servicios=3)
        use_case, tabla_km, pid = _armar([fila], [_siges(id_costo_servicios=7)])
        resultado = await use_case.execute(pid)
        assert resultado.vinculadas == 1
        assert tabla_km.rows[fila.id].id_costo_servicios == 7

    @pytest.mark.asyncio
    async def test_no_encontrada_queda_intacta_y_reportada(self) -> None:
        prestador_id = uuid.uuid4()
        fila = _fila(prestador_id, empresa="Cliente renombrado")
        use_case, tabla_km, pid = _armar([fila], [_siges()])
        antes = tabla_km.rows[fila.id]
        resultado = await use_case.execute(pid)
        assert resultado.no_encontradas == 1
        assert resultado.no_encontradas_detalle[0].empresa_nombre == "Cliente renombrado"
        assert tabla_km.rows[fila.id] is antes

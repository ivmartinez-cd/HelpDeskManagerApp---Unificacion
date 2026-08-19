"""AutoVincularMatchesN1TablaKm / ListarPropuestasN2TablaKm: matching de
sucursales Tabla KM ↔ Siges, niveles N1 (auto-vinculable) y N2 (propuesta,
requiere confirmación humana)."""

import uuid
from datetime import datetime
from uuid import UUID

import pytest

from src.modules.liquidaciones.application.use_cases.matching_sucursales_tabla_km import (
    AutoVincularMatchesN1TablaKm,
    ListarPropuestasN2TablaKm,
    MatchingSucursalesPorts,
)
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
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


def _fila(prestador_id: UUID, empresa: str, sucursal: str) -> TablaKm:
    return TablaKm(
        id=uuid.uuid4(),
        prestador_id=prestador_id,
        spst_id=None,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
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


def _siges(
    siges_id: int, empresa: str, sucursal: str, domicilio: str = "Calle 123"
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=siges_id,
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio=domicilio,
        localidad="San Juan",
        provincia="San Juan",
        id_costo_servicios=5,
    )


_Armado = tuple[
    MatchingSucursalesPorts, FakeTablaKmGeoRepository, FakeMatchingDescarteRepository, UUID, UUID
]


def _armar(empresa: str, sucursal: str, siges: list[SigesSucursalCliente]) -> _Armado:
    prestador_id = uuid.uuid4()
    prestador = make_prestador(id=prestador_id, siges_empresa_id=504, siges_base_sucursal_id=9)
    fila = _fila(prestador_id, empresa, sucursal)
    tabla_km = FakeTablaKmGeoRepository([fila])
    descartes = FakeMatchingDescarteRepository()
    ports = MatchingSucursalesPorts(
        prestadores=FakePrestadorRepository({prestador.id: prestador}),
        tabla_km=tabla_km,
        siges=FakeSigesGeoGateway(clientes=siges),
        descartes=descartes,
    )
    return ports, tabla_km, descartes, prestador_id, fila.id


class TestAutoVincularMatchesN1TablaKm:
    @pytest.mark.asyncio
    async def test_vincula_por_simbolo_numero(self) -> None:
        ports, tabla_km, _, pid, fila_id = _armar(
            "Gobierno de San Juan",
            "JINZ N°41 MANUEL LAINEZ",
            [_siges(1, "Gobierno de San Juan", "JINZ N.º 41 Manuel Lainez")],
        )

        resultado = await AutoVincularMatchesN1TablaKm(ports).execute(pid)

        assert resultado.vinculadas == 1
        actualizada = tabla_km.rows[fila_id]
        assert actualizada.siges_sucursal_id == 1
        assert actualizada.domicilio_cliente == "Calle 123"

    @pytest.mark.asyncio
    async def test_no_toca_candidatos_n2(self) -> None:
        ports, tabla_km, _, pid, fila_id = _armar(
            "Gobierno de San Juan",
            'Escuela Marcos Sastre "Emer"',
            [_siges(2, "Gobierno de San Juan", "Escuela rural Marcos Sastre")],
        )

        resultado = await AutoVincularMatchesN1TablaKm(ports).execute(pid)

        assert resultado.vinculadas == 0
        assert tabla_km.rows[fila_id].siges_sucursal_id is None

    @pytest.mark.asyncio
    async def test_idempotente_segunda_corrida_no_toca_nada(self) -> None:
        # Tras vincular, la fila queda con siges_sucursal_id — _sin_match_n0
        # la excluye directamente del pool en la corrida siguiente.
        ports, tabla_km, _, pid, fila_id = _armar(
            "Gobierno de San Juan",
            "JINZ N°41 MANUEL LAINEZ",
            [_siges(1, "Gobierno de San Juan", "JINZ N.º 41 Manuel Lainez")],
        )
        await AutoVincularMatchesN1TablaKm(ports).execute(pid)

        resultado = await AutoVincularMatchesN1TablaKm(ports).execute(pid)

        assert resultado.vinculadas == 0
        assert resultado.sin_cambios == 0
        assert resultado.detalle == []


class TestListarPropuestasN2TablaKm:
    @pytest.mark.asyncio
    async def test_propone_candidato_n2_con_motivo(self) -> None:
        ports, _, _, pid, fila_id = _armar(
            "Gobierno de San Juan",
            'Escuela Marcos Sastre "Emer"',
            [_siges(2, "Gobierno de San Juan", "Escuela rural Marcos Sastre")],
        )

        propuestas = await ListarPropuestasN2TablaKm(ports).execute(pid)

        assert len(propuestas) == 1
        assert propuestas[0].tabla_km_id == fila_id
        assert propuestas[0].candidatos[0].siges_sucursal_id == 2
        assert "emer" in propuestas[0].candidatos[0].motivo.lower()

    @pytest.mark.asyncio
    async def test_no_propone_lo_ya_vinculado_por_n1(self) -> None:
        ports, _, _, pid, _ = _armar(
            "Gobierno de San Juan",
            "JINZ N°41 MANUEL LAINEZ",
            [_siges(1, "Gobierno de San Juan", "JINZ N.º 41 Manuel Lainez")],
        )

        propuestas = await ListarPropuestasN2TablaKm(ports).execute(pid)

        assert propuestas == []

    @pytest.mark.asyncio
    async def test_no_repropone_fila_ya_vinculada_por_n1_en_corrida_previa(self) -> None:
        # Bug real detectado en el piloto SAN JUAN: tras auto-vincular N1, la
        # fila queda con siges_sucursal_id pero su nombre sigue sin matchear
        # N0 — sin el filtro por siges_sucursal_id, volvía a aparecer como
        # candidata N2 (ruido: pedía confirmar de nuevo algo ya resuelto).
        ports, _, _, pid, _ = _armar(
            "Gobierno de San Juan",
            "JINZ N°41 MANUEL LAINEZ",
            [_siges(1, "Gobierno de San Juan", "JINZ N.º 41 Manuel Lainez")],
        )
        await AutoVincularMatchesN1TablaKm(ports).execute(pid)

        propuestas = await ListarPropuestasN2TablaKm(ports).execute(pid)

        assert propuestas == []

    @pytest.mark.asyncio
    async def test_candidato_descartado_no_se_repropone(self) -> None:
        ports, _, descartes, pid, fila_id = _armar(
            "Gobierno de San Juan",
            'Escuela Marcos Sastre "Emer"',
            [_siges(2, "Gobierno de San Juan", "Escuela rural Marcos Sastre")],
        )
        await descartes.create(fila_id, 2, "operador@canaldirecto.com")

        propuestas = await ListarPropuestasN2TablaKm(ports).execute(pid)

        assert propuestas == []

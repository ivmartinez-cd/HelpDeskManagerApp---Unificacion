"""Tests del alta asistida de Tabla KM (BuscarSucursalesSiges, ADR-014 DS3)."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.siges_sucursales import (
    BuscarSucursalesSiges,
    SigesSucursalesPorts,
)
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    PrestadorSinVinculoSigesError,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_tabla_km
from tests.unit.domain.liquidaciones.fakes import FakeIncidenteRepository, FakeTablaKmRepository
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigPrestadorRepository,
    FakeSigesCatalogoGateway,
)


def _sucursal(
    sucursal_id: int, empresa: str, nombre: str, localidad: str | None = None
) -> SigesSucursalCliente:
    return SigesSucursalCliente(
        siges_sucursal_id=sucursal_id,
        empresa_nombre=empresa,
        sucursal_nombre=nombre,
        domicilio=None,
        localidad=localidad,
        provincia=None,
    )


def _ports(
    prestadores: FakeConfigPrestadorRepository,
    tabla_km: FakeTablaKmRepository | None = None,
    sucursales: dict[int, list[SigesSucursalCliente]] | None = None,
) -> SigesSucursalesPorts:
    return SigesSucursalesPorts(
        prestadores=prestadores,
        tabla_km=tabla_km or FakeTablaKmRepository(),
        siges=FakeSigesCatalogoGateway(sucursales=sucursales),
        incidentes=FakeIncidenteRepository(),
    )


async def test_marca_ya_cargada_con_comparacion_normalizada() -> None:
    prestador = make_prestador(nombre_corto="PENTACOM", siges_empresa_id=137)
    repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
    # Par existente con acento y mayúsculas distintas al de Siges.
    tabla_km = FakeTablaKmRepository(
        [
            make_tabla_km(
                prestador_id=prestador.id, empresa_nombre="ACHIRAS", sucursal_nombre="CP Achiras"
            )
        ]
    )
    sucursales = {
        137: [
            _sucursal(1, "Achiras", "CP Achiras"),
            _sucursal(2, "Banco Credicoop", "232 Los Boulevares"),
        ]
    }

    resultado = await BuscarSucursalesSiges(
        _ports(repo_p, tabla_km, sucursales)
    ).execute(prestador.id, q="")

    por_id = {s.siges_sucursal_id: s for s in resultado}
    assert por_id[1].ya_cargada
    assert not por_id[2].ya_cargada


async def test_filtra_por_q_en_empresa_o_sucursal() -> None:
    prestador = make_prestador(siges_empresa_id=137)
    repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
    sucursales = {
        137: [
            _sucursal(1, "Banco Credicoop", "Los Boulevares"),
            _sucursal(2, "Nutrien", "Agrocentro La Carlota"),
        ]
    }

    resultado = await BuscarSucursalesSiges(_ports(repo_p, sucursales=sucursales)).execute(
        prestador.id, q="credicoop"
    )

    assert [s.siges_sucursal_id for s in resultado] == [1]


async def test_prestador_sin_vinculo_lanza_error() -> None:
    prestador = make_prestador()
    repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})

    with pytest.raises(PrestadorSinVinculoSigesError):
        await BuscarSucursalesSiges(_ports(repo_p)).execute(prestador.id, q="")


async def test_prestador_inexistente_lanza_not_found() -> None:
    with pytest.raises(PrestadorNoEncontradoError):
        await BuscarSucursalesSiges(_ports(FakeConfigPrestadorRepository())).execute(
            uuid.uuid4(), q=""
        )

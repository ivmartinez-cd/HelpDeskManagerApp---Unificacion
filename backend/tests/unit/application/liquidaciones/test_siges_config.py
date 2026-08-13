"""Tests de los casos de uso de vínculo/sync contra Siges (ADR-014)."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.siges_config import (
    ProponerVinculosSiges,
    SigesConfigPorts,
    SyncConfigDesdeSiges,
    VincularPrestadorSiges,
    VincularSpstSiges,
)
from src.modules.liquidaciones.domain.errors import (
    PrestadorNoEncontradoError,
    SigesVinculoDuplicadoError,
    SpstNoEncontradoError,
)
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesEmpresaInfo,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_spst
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigPrestadorRepository,
    FakeConfigSpstRepository,
    FakeSigesCatalogoGateway,
)


def _empresa(
    siges_id: int, den: str, tipo: str = "PST", cuit: str | None = None
) -> SigesEmpresaInfo:
    return SigesEmpresaInfo(
        siges_empresa_id=siges_id,
        den_comercial=den,
        razon_social=None,
        cuit=cuit,
        tipo=tipo,  # type: ignore[arg-type]
    )


def _ports(
    prestadores: FakeConfigPrestadorRepository | None = None,
    spsts: FakeConfigSpstRepository | None = None,
    empresas: list[SigesEmpresaInfo] | None = None,
) -> SigesConfigPorts:
    return SigesConfigPorts(
        prestadores=prestadores or FakeConfigPrestadorRepository(),
        spsts=spsts or FakeConfigSpstRepository(),
        siges=FakeSigesCatalogoGateway(empresas),
    )


class TestProponerVinculos:
    async def test_propone_prestador_y_lista_disponibles(self) -> None:
        pentacom = make_prestador(nombre="Cordoba - Pentacom S.A.", nombre_corto="PENTACOM")
        repo = FakeConfigPrestadorRepository({pentacom.id: pentacom})
        empresas = [
            _empresa(137, "PST Cordoba - Pentacom S.A."),
            _empresa(333, "PST Esquel - Jorge Ismael Saiff"),
        ]

        resultado = await ProponerVinculosSiges(_ports(repo, empresas=empresas)).execute()

        assert [(p.local_id, p.siges_empresa_id) for p in resultado.propuestas] == [
            (pentacom.id, 137)
        ]
        assert [d.siges_empresa_id for d in resultado.disponibles] == [333]

    async def test_vinculados_no_se_reproponen(self) -> None:
        vinculado = make_prestador(
            nombre="Cordoba - Pentacom S.A.", nombre_corto="PENTACOM", siges_empresa_id=137
        )
        repo = FakeConfigPrestadorRepository({vinculado.id: vinculado})
        empresas = [_empresa(137, "PST Cordoba - Pentacom S.A.")]

        resultado = await ProponerVinculosSiges(_ports(repo, empresas=empresas)).execute()

        assert resultado.propuestas == []
        assert resultado.disponibles == []

    async def test_spst_solo_matchea_candidatos_spst(self) -> None:
        # El candidato PST (137) matchea por nombre pero es del tipo equivocado —
        # un SPST local solo se propone contra empresas SPST.
        spst = make_spst(nombre="Pentacom - Laboulaye")
        spsts = FakeConfigSpstRepository([spst])
        empresas = [
            _empresa(138, "SPST Pentacom - Laboulaye", tipo="SPST"),
            _empresa(137, "PST Cordoba - Pentacom S.A."),
        ]

        resultado = await ProponerVinculosSiges(_ports(spsts=spsts, empresas=empresas)).execute()

        assert [(p.entidad, p.siges_empresa_id) for p in resultado.propuestas] == [
            ("spst", 138)
        ]

    async def test_spst_sin_match_de_alta_confianza_no_se_propone(self) -> None:
        # Convención real: el nombre local trae al técnico ('Laboulaye - Roberto
        # Gil') y el de Siges al PST padre ('SPST Pentacom - Laboulaye') — sin
        # contención no hay propuesta; el vínculo se hace a mano desde disponibles.
        spst = make_spst(nombre="Laboulaye - Roberto Gil")
        spsts = FakeConfigSpstRepository([spst])
        empresas = [_empresa(138, "SPST Pentacom - Laboulaye", tipo="SPST")]

        resultado = await ProponerVinculosSiges(_ports(spsts=spsts, empresas=empresas)).execute()

        assert resultado.propuestas == []
        assert [d.siges_empresa_id for d in resultado.disponibles] == [138]


class TestVincular:
    async def test_vincular_y_desvincular_prestador(self) -> None:
        prestador = make_prestador()
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        use_case = VincularPrestadorSiges(_ports(repo))

        vinculado = await use_case.execute(prestador.id, siges_empresa_id=137)
        assert vinculado.siges_empresa_id == 137

        desvinculado = await use_case.execute(prestador.id, siges_empresa_id=None)
        assert desvinculado.siges_empresa_id is None

    async def test_prestador_inexistente(self) -> None:
        with pytest.raises(PrestadorNoEncontradoError):
            await VincularPrestadorSiges(_ports()).execute(uuid.uuid4(), siges_empresa_id=1)

    async def test_vinculo_duplicado(self) -> None:
        ya_vinculado = make_prestador(nombre_corto="UNO", siges_empresa_id=137)
        otro = make_prestador(nombre_corto="DOS")
        repo = FakeConfigPrestadorRepository({ya_vinculado.id: ya_vinculado, otro.id: otro})

        with pytest.raises(SigesVinculoDuplicadoError):
            await VincularPrestadorSiges(_ports(repo)).execute(otro.id, siges_empresa_id=137)

    async def test_vincular_spst_inexistente(self) -> None:
        with pytest.raises(SpstNoEncontradoError):
            await VincularSpstSiges(_ports()).execute(uuid.uuid4(), siges_empresa_id=1)


class TestSyncConfig:
    async def test_dry_run_reporta_cuit_sin_escribir(self) -> None:
        prestador = make_prestador(nombre_corto="PENTACOM", cuit=None, siges_empresa_id=137)
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        empresas = [_empresa(137, "PST Cordoba - Pentacom S.A.", cuit="30541232104")]

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=empresas)).execute(
            dry_run=True
        )

        assert [(c.campo, c.valor_nuevo) for c in resultado.cambios] == [("cuit", "30541232104")]
        assert repo.rows[prestador.id].cuit is None  # no escribió

    async def test_sync_real_actualiza_cuit(self) -> None:
        prestador = make_prestador(nombre_corto="PENTACOM", cuit=None, siges_empresa_id=137)
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        empresas = [_empresa(137, "PST Cordoba - Pentacom S.A.", cuit="30541232104")]

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=empresas)).execute(
            dry_run=False
        )

        assert not resultado.dry_run
        assert repo.rows[prestador.id].cuit == "30541232104"

    async def test_cuit_igual_con_otro_formato_no_es_cambio(self) -> None:
        prestador = make_prestador(cuit="30-54123210-4", siges_empresa_id=137)
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        empresas = [_empresa(137, "PST X", cuit="30541232104")]

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=empresas)).execute(
            dry_run=False
        )

        assert resultado.cambios == []
        assert resultado.sin_cambios == 1
        assert repo.rows[prestador.id].cuit == "30-54123210-4"  # formato local intacto

    async def test_siges_sin_cuit_no_borra_el_local(self) -> None:
        prestador = make_prestador(cuit="30-1", siges_empresa_id=137)
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        empresas = [_empresa(137, "PST X", cuit=None)]

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=empresas)).execute(
            dry_run=False
        )

        assert resultado.cambios == []
        assert repo.rows[prestador.id].cuit == "30-1"

    async def test_sin_vinculo_y_vinculo_roto(self) -> None:
        sin_vinculo = make_prestador(nombre_corto="SUELTO")
        roto = make_prestador(nombre_corto="ROTO", siges_empresa_id=999)
        repo = FakeConfigPrestadorRepository({sin_vinculo.id: sin_vinculo, roto.id: roto})

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=[])).execute(dry_run=True)

        assert resultado.sin_vinculo == ["SUELTO"]
        assert resultado.vinculo_roto == ["ROTO"]

    async def test_nombre_distinto_se_reporta_sin_escribir(self) -> None:
        prestador = make_prestador(
            nombre="Supernova Servicios S.R.L.", nombre_corto="PERTEX", siges_empresa_id=600
        )
        repo = FakeConfigPrestadorRepository({prestador.id: prestador})
        empresas = [_empresa(600, "PST Rosario - Supernova Servicios SRL")]

        resultado = await SyncConfigDesdeSiges(_ports(repo, empresas=empresas)).execute(
            dry_run=False
        )

        assert [d.siges_den_comercial for d in resultado.nombres_distintos] == [
            "PST Rosario - Supernova Servicios SRL"
        ]
        assert repo.rows[prestador.id].nombre == "Supernova Servicios S.R.L."

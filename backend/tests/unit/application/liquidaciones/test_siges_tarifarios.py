"""Tests de los casos de uso de sync de tarifarios/zonas contra Siges (ADR-014)."""

import uuid
from datetime import date

import pytest

from src.modules.liquidaciones.application.use_cases.siges_tarifarios import (
    EstadoZonasSiges,
    MapearZonaSiges,
    SigesTarifariosPorts,
    SyncTarifariosDesdeSiges,
)
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
)
from tests.unit.domain.liquidaciones.factories import make_prestador, make_spst, make_tarifario
from tests.unit.domain.liquidaciones.fakes_config import (
    FakeConfigPrestadorRepository,
    FakeConfigSpstRepository,
    FakeConfigTarifarioRepository,
    FakeSigesCatalogoGateway,
    FakeTarifarioZonaMapRepository,
)


def _costo(
    empresa: int = 137,
    descripcion: str = "Genérica",
    vigencia: date = date(2026, 7, 1),
    correctivo: float = 67820.0,
) -> SigesCostoServicio:
    return SigesCostoServicio(
        siges_empresa_id=empresa,
        descripcion=descripcion,
        vigencia_desde=vigencia,
        costo_km=758.96,
        correctivo=correctivo,
        preventivo=0.0,
        instalacion=0.0,
        pre_correctivo=0.0,
        guardia=0.0,
        sistemas=0.0,
    )


def _ports(
    prestadores: FakeConfigPrestadorRepository,
    tarifarios: FakeConfigTarifarioRepository | None = None,
    zona_maps: FakeTarifarioZonaMapRepository | None = None,
    costos: list[SigesCostoServicio] | None = None,
    spsts: FakeConfigSpstRepository | None = None,
) -> SigesTarifariosPorts:
    return SigesTarifariosPorts(
        prestadores=prestadores,
        tarifarios=tarifarios or FakeConfigTarifarioRepository(),
        spsts=spsts or FakeConfigSpstRepository(),
        zona_maps=zona_maps or FakeTarifarioZonaMapRepository(),
        siges=FakeSigesCatalogoGateway(costos=costos),
    )


class TestSyncTarifarios:
    async def test_dry_run_reporta_sin_escribir(self) -> None:
        prestador = make_prestador(nombre_corto="PENTACOM", siges_empresa_id=137)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        repo_t = FakeConfigTarifarioRepository()

        resultado = await SyncTarifariosDesdeSiges(
            _ports(repo_p, repo_t, costos=[_costo()])
        ).execute(dry_run=True)

        assert resultado.creados == 1
        assert [(g.tipo_servicio, g.zona, g.cantidad) for g in resultado.grupos_creados] == [
            ("correctivo", None, 1)
        ]
        assert repo_t.rows == []  # no escribió

    async def test_sync_real_crea_y_recadena_vigencias(self) -> None:
        prestador = make_prestador(nombre_corto="PENTACOM", siges_empresa_id=137)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        repo_t = FakeConfigTarifarioRepository()
        costos = [
            _costo(vigencia=date(2026, 4, 1), correctivo=63522.0),
            _costo(vigencia=date(2026, 7, 1), correctivo=67820.0),
        ]

        resultado = await SyncTarifariosDesdeSiges(_ports(repo_p, repo_t, costos=costos)).execute(
            dry_run=False
        )

        assert resultado.creados == 2
        assert len(repo_t.rows) == 2
        por_desde = {t.vigencia_desde: t for t in repo_t.rows}
        # El recadenado de CreateTarifario cerró la vigencia anterior.
        assert por_desde[date(2026, 4, 1)].vigencia_hasta == date(2026, 6, 30)
        assert por_desde[date(2026, 7, 1)].vigencia_hasta is None

    async def test_conflicto_se_reporta_y_no_pisa(self) -> None:
        prestador = make_prestador(nombre_corto="PENTACOM", siges_empresa_id=137)
        existente = make_tarifario(
            prestador_id=prestador.id,
            tipo_servicio="correctivo",
            zona=None,
            costo_servicio=60000.0,
            costo_km=758.96,
            vigencia_desde=date(2026, 7, 1),
        )
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        repo_t = FakeConfigTarifarioRepository([existente])

        resultado = await SyncTarifariosDesdeSiges(
            _ports(repo_p, repo_t, costos=[_costo()])
        ).execute(dry_run=False)

        assert resultado.creados == 0
        assert [(c.prestador, c.campo, c.valor_siges) for c in resultado.conflictos] == [
            ("PENTACOM", "costo_servicio", 67820.0)
        ]
        assert repo_t.rows[0].costo_servicio == 60000.0  # intacto

    async def test_zona_sin_mapear_se_reporta_y_no_crea(self) -> None:
        prestador = make_prestador(nombre_corto="INFOMAC", siges_empresa_id=740)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        repo_t = FakeConfigTarifarioRepository()
        costos = [_costo(empresa=740, descripcion="Ushuaia - Infomac")]

        resultado = await SyncTarifariosDesdeSiges(_ports(repo_p, repo_t, costos=costos)).execute(
            dry_run=False
        )

        assert resultado.creados == 0
        assert [(z.prestador, z.descripcion_siges) for z in resultado.zonas_sin_mapear] == [
            ("INFOMAC", "Ushuaia - Infomac")
        ]
        assert repo_t.rows == []

    async def test_prestador_sin_vinculo_queda_fuera(self) -> None:
        prestador = make_prestador(nombre_corto="SUELTO")
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})

        resultado = await SyncTarifariosDesdeSiges(_ports(repo_p, costos=[_costo()])).execute(
            dry_run=True
        )

        assert resultado.creados == 0
        assert resultado.prestadores_sin_vinculo == ["SUELTO"]


class TestEstadoZonas:
    async def test_reporta_propuesta_y_mapeo_existente(self) -> None:
        prestador = make_prestador(nombre_corto="INFOMAC", siges_empresa_id=740)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        repo_t = FakeConfigTarifarioRepository(
            [make_tarifario(prestador_id=prestador.id, zona="Ushuaia")]
        )
        zona_maps = FakeTarifarioZonaMapRepository()
        await zona_maps.upsert(
            prestador_id=prestador.id,
            descripcion_siges="Villa Mercedes / Rio IV",
            zona_local="Villa Mercedes",
        )
        costos = [
            _costo(empresa=740, descripcion="Ushuaia - Infomac"),
            _costo(empresa=740, descripcion="Villa Mercedes / Rio IV"),
            _costo(empresa=740, descripcion="Genérica"),
        ]

        resultado = await EstadoZonasSiges(
            _ports(repo_p, repo_t, zona_maps, costos=costos)
        ).execute()

        por_descripcion = {z.descripcion_siges: z for z in resultado.zonas}
        assert set(por_descripcion) == {"Ushuaia - Infomac", "Villa Mercedes / Rio IV"}
        assert not por_descripcion["Ushuaia - Infomac"].mapeada
        assert por_descripcion["Ushuaia - Infomac"].propuesta == "Ushuaia"
        assert por_descripcion["Villa Mercedes / Rio IV"].mapeada
        assert por_descripcion["Villa Mercedes / Rio IV"].zona_local == "Villa Mercedes"

    async def test_propone_zona_de_spst_aunque_no_tenga_tarifa_cargada(self) -> None:
        """Antes solo se ofrecían zonas ya usadas en `Tarifario` — obligaba a cargar
        una tarifa "semilla" a mano antes de poder mapear. Ahora el catálogo de
        zonas candidatas sale directo de los SPST del prestador."""
        prestador = make_prestador(nombre_corto="SAN JUAN", siges_empresa_id=850)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        spsts = FakeConfigSpstRepository(
            [make_spst(prestador_id=prestador.id, zona="Valle Fértil")]
        )
        costos = [_costo(empresa=850, descripcion="GSJ - Escuelas Valle Fertil")]

        resultado = await EstadoZonasSiges(
            _ports(repo_p, spsts=spsts, costos=costos)
        ).execute()

        zona = resultado.zonas[0]
        assert zona.zonas_locales == ["Valle Fértil"]

    async def test_mapeo_a_generica_se_distingue_de_sin_mapear(self) -> None:
        prestador = make_prestador(nombre_corto="MENDOZA", siges_empresa_id=657)
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        zona_maps = FakeTarifarioZonaMapRepository()
        await zona_maps.upsert(
            prestador_id=prestador.id, descripcion_siges="TMTB122", zona_local=None
        )
        costos = [_costo(empresa=657, descripcion="TMTB122")]

        resultado = await EstadoZonasSiges(
            _ports(repo_p, zona_maps=zona_maps, costos=costos)
        ).execute()

        assert len(resultado.zonas) == 1
        assert resultado.zonas[0].mapeada
        assert resultado.zonas[0].zona_local is None


class TestMapearZona:
    async def test_upsert_y_normalizacion(self) -> None:
        prestador = make_prestador()
        repo_p = FakeConfigPrestadorRepository({prestador.id: prestador})
        zona_maps = FakeTarifarioZonaMapRepository()

        mapa = await MapearZonaSiges(_ports(repo_p, zona_maps=zona_maps)).execute(
            prestador.id, descripcion_siges="  Ushuaia - Infomac ", zona_local=" Ushuaia "
        )

        assert (mapa.descripcion_siges, mapa.zona_local) == ("Ushuaia - Infomac", "Ushuaia")

    async def test_prestador_inexistente(self) -> None:
        with pytest.raises(PrestadorNoEncontradoError):
            await MapearZonaSiges(_ports(FakeConfigPrestadorRepository())).execute(
                uuid.uuid4(), descripcion_siges="X", zona_local="Y"
            )

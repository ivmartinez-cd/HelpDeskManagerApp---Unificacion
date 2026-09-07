"""Tests del matching de propuesta de vínculo local ↔ Siges (ADR-014)."""

import uuid

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesEmpresaInfo,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    marca_prestador,
    normalizar_nombre,
    proponer_vinculos,
    spsts_siges_del_prestador,
)


def _empresa(siges_id: int, den: str, tipo: str = "PST") -> SigesEmpresaInfo:
    return SigesEmpresaInfo(
        siges_empresa_id=siges_id,
        den_comercial=den,
        razon_social=None,
        cuit=None,
        tipo=tipo,  # type: ignore[arg-type]
    )


class TestNormalizarNombre:
    def test_saca_prefijo_pst_acentos_y_puntuacion(self) -> None:
        assert normalizar_nombre("PST Córdoba - Pentacom S.A.") == "cordoba pentacom s a"

    def test_saca_prefijo_spst(self) -> None:
        assert normalizar_nombre("SPST Pentacom - Laboulaye") == "pentacom laboulaye"

    def test_prefijo_solo_como_token_inicial(self) -> None:
        # "pst" en el medio del nombre no es prefijo
        assert normalizar_nombre("Empresa PST SRL") == "empresa pst srl"


class TestProponerVinculos:
    def test_match_exacto_normalizado(self) -> None:
        local_id = uuid.uuid4()
        candidatos = [_empresa(137, "PST Cordoba - Pentacom S.A.")]

        propuestas = proponer_vinculos([(local_id, "Córdoba - Pentacom S.A.")], candidatos)

        assert propuestas == {local_id: 137}

    def test_match_por_contencion(self) -> None:
        # PERTEX local: 'Supernova Servicios S.R.L.' ⊂ 'PST Rosario - Supernova Servicios SRL'
        local_id = uuid.uuid4()
        candidatos = [_empresa(600, "PST Rosario - Supernova Servicios SRL")]

        propuestas = proponer_vinculos([(local_id, "Supernova Servicios S.R.L.")], candidatos)

        assert propuestas == {local_id: 600}

    def test_ambiguedad_por_local_no_propone(self) -> None:
        local_id = uuid.uuid4()
        candidatos = [
            _empresa(1, "PST Bariloche - Infomac"),
            _empresa(2, "PST Neuquen - Infomac"),
        ]

        assert proponer_vinculos([(local_id, "Infomac")], candidatos) == {}

    def test_ambiguedad_por_candidato_no_propone(self) -> None:
        # Dos locales matchean el mismo candidato → se descartan ambos.
        candidatos = [_empresa(740, "PST Villa Mercedes - Infomac")]
        locales = [
            (uuid.uuid4(), "Villa Mercedes - Infomac"),
            (uuid.uuid4(), "Infomac"),
        ]

        assert proponer_vinculos(locales, candidatos) == {}

    def test_sin_match_no_propone(self) -> None:
        propuestas = proponer_vinculos(
            [(uuid.uuid4(), "Catamarca - Click")], [_empresa(9, "PST Trelew - Copytec")]
        )

        assert propuestas == {}


class TestSpstsSigesDelPrestador:
    """Nombres reales de Siges (2026-09-07): espacios dobles, minúsculas y
    guión pegado en las SPST de Infomac; 'S.A.' en el nombre de Pentacom."""

    def test_marca_es_el_primer_token_del_nombre_del_pst(self) -> None:
        assert marca_prestador("PST Villa Mercedes - Infomac") == "infomac"
        assert marca_prestador("PST Cordoba - Pentacom S.A.") == "pentacom"
        assert marca_prestador("PST Rosario - Supernova Servicios SRL") == "supernova"
        assert marca_prestador("PST ") is None

    def test_agrupa_las_spst_por_marca_tolerando_el_formato(self) -> None:
        empresas = [
            _empresa(740, "PST Villa Mercedes - Infomac"),
            _empresa(1405, "SPST  Infomac - Neuquen", "SPST"),
            _empresa(1143, "SPST infomac -  Merlo", "SPST"),
            _empresa(1243, "SPST Infomac-  Pehuajo", "SPST"),
            _empresa(1271, "SPST Infomac - Santa Rosa", "SPST"),
            _empresa(600, "PST Rosario - Supernova Servicios SRL"),
            _empresa(601, "SPST Supernova - Rafaela", "SPST"),
            _empresa(1086, "SPST AISA - El Dorado", "SPST"),
        ]
        infomac = spsts_siges_del_prestador("PST Villa Mercedes - Infomac", empresas)
        assert [e.siges_empresa_id for e in infomac] == [1405, 1143, 1243, 1271]
        supernova = spsts_siges_del_prestador("PST Rosario - Supernova Servicios SRL", empresas)
        assert [e.siges_empresa_id for e in supernova] == [601]
        assert spsts_siges_del_prestador("PST Caleta - AISA", empresas) == [empresas[7]]

    def test_ignora_pst_aunque_compartan_marca(self) -> None:
        empresas = [
            _empresa(740, "PST Villa Mercedes - Infomac"),
            _empresa(741, "PST Infomac - Otra zona"),
        ]
        assert spsts_siges_del_prestador("PST Villa Mercedes - Infomac", empresas) == []

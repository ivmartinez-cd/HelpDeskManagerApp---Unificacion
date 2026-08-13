"""Tests del matching de propuesta de vínculo local ↔ Siges (ADR-014)."""

import uuid

from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesEmpresaInfo,
)
from src.modules.liquidaciones.domain.services.vinculacion_siges import (
    normalizar_nombre,
    proponer_vinculos,
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

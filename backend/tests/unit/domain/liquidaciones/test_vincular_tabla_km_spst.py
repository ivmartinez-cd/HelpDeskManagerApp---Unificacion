"""Tests de la heurística de matching Tabla KM ↔ SPST por localidad."""

from src.modules.liquidaciones.domain.services.vincular_tabla_km_spst import (
    proponer_vinculos_spst,
)
from tests.unit.domain.liquidaciones.factories import make_spst, make_tabla_km


class TestProponerVinculosSpst:
    def test_matchea_por_substring_ignorando_acentos(self) -> None:
        spst = make_spst(zona_cobertura="Valle Fértil")
        fila = make_tabla_km(localidad_cliente="SAN AGUSTIN DEL VALLE FERTIL")

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert len(propuestas) == 1
        assert propuestas[0].spst_id == spst.id
        assert propuestas[0].spst_nombre == spst.nombre

    def test_fila_ya_vinculada_no_se_propone(self) -> None:
        spst = make_spst(zona_cobertura="Valle Fértil")
        fila = make_tabla_km(localidad_cliente="Valle Fertil", spst_id=spst.id)

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert propuestas == []

    def test_ambiguo_entre_dos_spst_no_propone(self) -> None:
        s1 = make_spst(zona_cobertura="San Juan")
        s2 = make_spst(zona_cobertura="San Juan Capital")
        fila = make_tabla_km(localidad_cliente="San Juan Capital Centro")

        propuestas = proponer_vinculos_spst([fila], [s1, s2])

        assert propuestas[0].spst_id is None

    def test_sin_localidad_no_propone(self) -> None:
        spst = make_spst(zona_cobertura="Valle Fértil")
        fila = make_tabla_km(localidad_cliente=None)

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert propuestas[0].spst_id is None

    def test_sin_match_no_propone(self) -> None:
        spst = make_spst(zona_cobertura="Valle Fértil")
        fila = make_tabla_km(localidad_cliente="San Rafael")

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert propuestas[0].spst_id is None

    def test_usa_localidad_del_spst_cuando_no_tiene_zona(self) -> None:
        spst = make_spst(zona_cobertura=None, localidad="Villa Mercedes")
        fila = make_tabla_km(localidad_cliente="Villa Mercedes Centro")

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert propuestas[0].spst_id == spst.id

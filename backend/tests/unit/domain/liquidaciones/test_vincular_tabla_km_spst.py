"""Tests de la heurística de matching Tabla KM ↔ SPST por localidad."""

from src.modules.liquidaciones.domain.services.vincular_tabla_km_spst import (
    CRITERIO_LOCALIDAD,
    CRITERIO_PROVINCIA,
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

    def test_sin_match_por_localidad_propone_por_provincia_unica(self) -> None:
        gral_roca = make_spst(zona_cobertura="Gral. Roca / Neuquén", provincia="Río Negro")
        norte = make_spst(zona_cobertura="Chos Malal - Barrancas", provincia="Neuquén")
        fila = make_tabla_km(localidad_cliente="Cipolletti", provincia_cliente="Rio Negro")

        propuestas = proponer_vinculos_spst([fila], [gral_roca, norte])

        assert propuestas[0].spst_id == gral_roca.id
        assert propuestas[0].criterio == CRITERIO_PROVINCIA

    def test_provincia_ambigua_entre_dos_spst_no_propone(self) -> None:
        s1 = make_spst(zona_cobertura="Rosario", provincia="Santa Fe")
        s2 = make_spst(zona_cobertura="Rafaela", provincia="Santa Fe")
        fila = make_tabla_km(localidad_cliente="Venado Tuerto", provincia_cliente="Santa Fe")

        propuestas = proponer_vinculos_spst([fila], [s1, s2])

        assert propuestas[0].spst_id is None

    def test_localidad_gana_sobre_provincia(self) -> None:
        gral_roca = make_spst(zona_cobertura="Gral. Roca / Neuquén", provincia="Río Negro")
        norte = make_spst(zona_cobertura="Chos Malal - Barrancas", provincia="Neuquén")
        fila = make_tabla_km(localidad_cliente="Neuquén", provincia_cliente="Neuquén")

        propuestas = proponer_vinculos_spst([fila], [gral_roca, norte])

        assert propuestas[0].spst_id == gral_roca.id
        assert propuestas[0].criterio == CRITERIO_LOCALIDAD

    def test_sin_provincia_en_spst_no_propone_por_provincia(self) -> None:
        spst = make_spst(zona_cobertura="Valle Fértil", provincia=None)
        fila = make_tabla_km(localidad_cliente="San Rafael", provincia_cliente="San Juan")

        propuestas = proponer_vinculos_spst([fila], [spst])

        assert propuestas[0].spst_id is None

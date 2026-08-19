from src.modules.liquidaciones.domain.services.geovalidacion_tier1 import (
    provincias_compatibles,
)


class TestProvinciasCompatibles:
    def test_iguales_sin_acentos_ni_mayusculas(self) -> None:
        assert provincias_compatibles("San Juan", "San Juan") is True
        assert provincias_compatibles("SAN JUAN", "san juan") is True

    def test_distintas_no_compatibles(self) -> None:
        assert provincias_compatibles("San Juan", "Mendoza") is False

    def test_declarada_vacia_o_none_siempre_compatible(self) -> None:
        assert provincias_compatibles(None, "San Juan") is True
        assert provincias_compatibles("", "San Juan") is True
        assert provincias_compatibles("   ", "San Juan") is True

    def test_alias_caba(self) -> None:
        assert provincias_compatibles("CABA", "Ciudad Autónoma de Buenos Aires") is True
        assert provincias_compatibles("Capital Federal", "Ciudad Autónoma de Buenos Aires") is True

    def test_con_tilde_vs_sin_tilde(self) -> None:
        assert provincias_compatibles("Córdoba", "Cordoba") is True

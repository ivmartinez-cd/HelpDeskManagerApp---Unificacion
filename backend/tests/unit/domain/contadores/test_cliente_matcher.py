"""Tests del cruce cliente de Gestión → Empresa de Siges (cliente_matcher)."""

from src.modules.contadores.domain.ports.parque_cliente_port import EmpresaSiges
from src.modules.contadores.domain.services.cliente_matcher import (
    IndiceNombres,
    buscar_por_nombre,
    match_clientes,
    normalizar_nombre,
)


def test_normaliza_acentos_mayusculas_y_puntuacion() -> None:
    assert normalizar_nombre("  Aerolíneas  Argentinas S.A. ") == "AEROLINEAS ARGENTINAS SA"


def test_match_exacto_normalizado() -> None:
    empresas = [EmpresaSiges(id=10, den_comercial="Aerolineas Argentinas")]
    resultado = match_clientes(["Aerolíneas Argentinas"], empresas, alias={})
    assert resultado == {"Aerolíneas Argentinas": [10]}


def test_exacto_ambiguo_no_cruza() -> None:
    # Caso real: 'Resmacón' (88) y 'Resmacon' (1147) activas a la vez.
    empresas = [
        EmpresaSiges(id=1, den_comercial="Plastiferro"),
        EmpresaSiges(id=2, den_comercial="PLASTIFERRO"),
    ]
    assert match_clientes(["Plastiferro"], empresas, alias={}) == {"Plastiferro": []}


def test_contencion_unica_cruza() -> None:
    empresas = [
        EmpresaSiges(id=5, den_comercial="Banco Santander Río Argentina"),
        EmpresaSiges(id=6, den_comercial="Otro Banco"),
    ]
    resultado = match_clientes(["Banco Santander Rio"], empresas, alias={})
    assert resultado == {"Banco Santander Rio": [5]}


def test_contencion_ambigua_no_cruza() -> None:
    empresas = [
        EmpresaSiges(id=5, den_comercial="Banco Nacion Casa Central"),
        EmpresaSiges(id=6, den_comercial="Banco Nacion Sucursales"),
    ]
    assert match_clientes(["Banco Nacion"], empresas, alias={}) == {"Banco Nacion": []}


def test_nombre_corto_no_intenta_contencion() -> None:
    # 'BIND' (4 chars) está contenido en muchas denominaciones — el mínimo de
    # 5 caracteres evita falsos positivos.
    empresas = [EmpresaSiges(id=7, den_comercial="BIND Banco Industrial")]
    assert match_clientes(["BIND"], empresas, alias={}) == {"BIND": []}


def test_contencion_no_matchea_substring_dentro_de_una_palabra() -> None:
    # Caso real 2026-09-03: 'ADIUM' (grupo Siges, laboratorio) es substring
    # de 'ARCADIUM' pero no está contenido como palabra completa en
    # 'Arcadium Lithium' (minera de litio, cliente distinto) — no debe cruzar.
    empresas = [EmpresaSiges(id=439, den_comercial="ADIUM")]
    assert match_clientes(["Arcadium Lithium"], empresas, alias={}) == {
        "Arcadium Lithium": []
    }


def test_alias_manual_gana_sobre_el_cruce_automatico() -> None:
    empresas = [EmpresaSiges(id=8, den_comercial="Gob San Juan SRL")]
    resultado = match_clientes(
        ["Gob San Juan"], empresas, alias={"Gob San Juan": [999]}
    )
    assert resultado == {"Gob San Juan": [999]}


def test_alias_compara_normalizado() -> None:
    # El alias sobrevive a cambios de mayúsculas/acentos en Gestión.
    resultado = match_clientes(["GOB SAN JUÁN"], [], alias={"Gob San Juan": [999]})
    assert resultado == {"GOB SAN JUÁN": [999]}


def test_alias_multiempresa_devuelve_todas() -> None:
    # 'Salta Refrescos' son 3 regiones en Siges: el cliente suma las tres.
    resultado = match_clientes(
        ["Salta Refrescos"], [], alias={"Salta Refrescos": [68, 69, 585]}
    )
    assert resultado == {"Salta Refrescos": [68, 69, 585]}


class TestBuscarPorNombre:
    """Cruce genérico de nombres libres (grupo Siges ↔ cliente Gestión):
    exacto > flex (separadores) > contención única; ambiguo o corto queda
    sin cruce."""

    def _indice(self, nombres: dict[str, str]) -> IndiceNombres[str]:
        return IndiceNombres({normalizar_nombre(k): v for k, v in nombres.items()})

    def test_match_exacto(self) -> None:
        indice = self._indice({"Chubb": "Barbara Romero"})
        assert buscar_por_nombre("Chubb", indice) == "Barbara Romero"

    def test_flex_equipara_separadores(self) -> None:
        indice = self._indice({"Roemmers / Maprimed": "Soledad Miguez"})
        assert buscar_por_nombre("Roemmers - Maprimed", indice) == "Soledad Miguez"

    def test_contencion_unica(self) -> None:
        indice = self._indice({"Galicia Seguros Retiro": "Op A", "Chubb": "Op B"})
        assert buscar_por_nombre("Galicia Seguros", indice) == "Op A"

    def test_contencion_ambigua_queda_sin_cruce(self) -> None:
        indice = self._indice({"Galicia Seguros": "Op A", "Galicia Retiro": "Op B"})
        assert buscar_por_nombre("Galicia", indice) is None

    def test_nombre_corto_no_matchea_por_contencion(self) -> None:
        indice = self._indice({"ASP Logistica Central": "Op A"})
        assert buscar_por_nombre("ASP", indice) is None

    def test_no_matchea_substring_dentro_de_una_palabra(self) -> None:
        # Caso real: grupo Siges 'ADIUM' (laboratorio) contra cliente de
        # calendario 'Arcadium Lithium' (minera de litio, sin relación).
        indice = self._indice({"Arcadium Lithium": "Op A"})
        assert buscar_por_nombre("ADIUM", indice) is None

    def test_sin_nombre_o_sin_indice(self) -> None:
        assert buscar_por_nombre(None, self._indice({"Chubb": "Op"})) is None
        assert buscar_por_nombre("Chubb", self._indice({})) is None

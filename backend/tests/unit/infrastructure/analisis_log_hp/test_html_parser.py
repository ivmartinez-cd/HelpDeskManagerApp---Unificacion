"""Parseo HTML/XML del portal SDS: tabla de event logs → TSV, URLs de ayuda,
tabla de operaciones HP Smart, resultado de búsqueda por serial y form de
refresh de caché."""

import pytest

from src.modules.analisis_log_hp.infrastructure.hp_portal.html_parser import (
    _get_html_content,
    extract_device_id,
    extract_help_urls,
    extract_model_name,
    html_to_tsv,
    parse_cache_refresh_form,
    parse_hp_operations,
)
from src.shared.domain.errors import ExternalServiceError

_TABLA = """
<table class="data"><thead><tr><th>Tipo</th></tr></thead><tbody>
<tr><td>Error</td><td>13.20.01</td><td>05-ago-2026 09:05:00</td><td>100</td>
    <td>FW</td><td><a href="http://help/13">Atasco de papel</a></td></tr>
<tr><td>Info</td><td>INFO1</td><td>05-ago-2026 10:00:00</td><td>101</td></tr>
<tr><td>Error</td><td>13.20.01</td><td>06-ago-2026 09:05:00</td><td>102</td>
    <td>FW</td><td><a href="http://help/otro">Otra</a></td></tr>
<tr><td>Warning</td><td>41.03</td><td>06-ago-2026 10:05:00</td><td>103</td>
    <td>FW</td><td>sin link</td></tr>
<tr><td>Warning</td><td>41.04</td><td>06-ago-2026 10:05:00</td><td>103</td>
    <td>FW</td><td><a>sin href</a></td></tr>
</tbody></table>
"""
_XML = f"<response><content><![CDATA[{_TABLA}]]></content></response>"


class TestGetHtmlContent:
    def test_desenvuelve_el_nodo_content(self) -> None:
        assert "13.20.01" in _get_html_content(_XML)

    def test_xml_roto_cae_al_cdata_mas_largo(self) -> None:
        raw = "<a><![CDATA[corto]]><![CDATA[mucho mas largo]]>"
        assert _get_html_content(raw) == "mucho mas largo"

    def test_sin_cdata_devuelve_el_texto_crudo(self) -> None:
        assert _get_html_content("<p>plano</p") == "<p>plano</p"


class TestHtmlToTsv:
    def test_genera_header_y_seis_columnas_por_fila(self) -> None:
        tsv = html_to_tsv(_XML)
        lineas = tsv.splitlines()
        assert lineas[0].startswith("Tipo de evento\tCódigo de evento")
        assert lineas[1] == "Error\t13.20.01\t05-ago-2026 09:05:00\t100\tFW\tAtasco de papel"
        assert lineas[2] == "Info\tINFO1\t05-ago-2026 10:00:00\t101\t\t"
        assert len(lineas) == 6

    def test_acepta_html_plano_con_tabla_sin_clase(self) -> None:
        html = "<table><tbody><tr><td>Error</td><td>X</td></tr></tbody></table>"
        assert html_to_tsv(html).splitlines()[1] == "Error\tX\t\t\t\t"

    def test_sin_tabla_o_vacio_devuelve_vacio(self) -> None:
        assert html_to_tsv("<response><content><![CDATA[<p>nada</p>]]></content></response>") == ""
        assert html_to_tsv("<response><content><![CDATA[   ]]></content></response>") == ""

    def test_xml_roto_usa_fallback_cdata(self) -> None:
        roto = f"<response><content><![CDATA[{_TABLA}]]></content>"
        assert "13.20.01" in html_to_tsv(roto)


class TestExtractHelpUrls:
    def test_primer_link_por_codigo_con_descripcion(self) -> None:
        urls = extract_help_urls(_XML)
        assert urls == {"13.20.01": {"url": "http://help/13", "description": "Atasco de papel"}}

    def test_entrada_no_html_devuelve_vacio(self) -> None:
        assert extract_help_urls("") == {}


class TestParseHpOperations:
    def test_mapea_celdas_a_campos_ignorando_links(self) -> None:
        html = """
        <table><tr><th>h</th></tr>
        <tr><td>RefreshHPCloudDeviceActionCache <a href="#">ver</a></td><td>hoy</td>
            <td>yo</td><td>ok</td><td>ayer</td><td>antes</td></tr>
        <tr><td></td><td>x</td><td>y</td><td>z</td></tr>
        <tr><td>corta</td></tr>
        </table>"""
        ops = parse_hp_operations(html)
        assert ops == [{
            "operation": "RefreshHPCloudDeviceActionCache", "sent": "hoy", "sent_by": "yo",
            "last_known_state": "ok", "last_state_updated": "ayer",
            "last_state_requested": "antes",
        }]

    def test_celda_solo_con_link_usa_el_texto_del_link(self) -> None:
        html = "<table><tr><td><a>OpLink</a></td><td>a</td><td>b</td><td>c</td></tr></table>"
        assert parse_hp_operations(html)[0]["operation"] == "OpLink"

    def test_entrada_vacia_devuelve_lista_vacia(self) -> None:
        assert parse_hp_operations("") == []


class TestExtractModelName:
    def test_por_regex_normaliza_espacios(self) -> None:
        page = '<a class="entity-name model" href="#">  HP   LaserJet\n M404 </a>'
        assert extract_model_name(page) == "HP LaserJet M404"

    def test_por_xpath_si_el_regex_no_matchea(self) -> None:
        page = '<a class="model entity-name"><span>Modelo</span> B</a>'
        assert extract_model_name(page) == "Modelo B"

    def test_sin_link_de_modelo_devuelve_default(self) -> None:
        assert extract_model_name("<p>nada</p>") == "Generico / Desconocido"

    def test_html_no_parseable_devuelve_default_sin_propagar(self) -> None:
        assert extract_model_name("") == "Generico / Desconocido"


class TestExtractDeviceId:
    def test_prefiere_la_url_final_de_la_redireccion(self) -> None:
        assert extract_device_id("https://x/devices/4242/hpsmart", 'href="/devices/1"') == "4242"

    def test_url_sin_id_numerico_cae_al_html(self) -> None:
        assert extract_device_id("https://x/devices/abc", 'href="/devices/99"') == "99"

    def test_sin_id_en_ningun_lado_devuelve_none(self) -> None:
        assert extract_device_id("https://x/search", "<p>sin resultados</p>") is None


class TestParseCacheRefreshForm:
    def test_action_relativa_se_vuelve_absoluta_con_csrf(self) -> None:
        page = (
            '<form action="/PortalWeb/devices/7/hpsmart/refresh/hpcache">'
            '<input name="__csrftoken" value="tok"/></form>'
        )
        assert parse_cache_refresh_form(page, origin="https://o") == (
            "https://o/PortalWeb/devices/7/hpsmart/refresh/hpcache", {"__csrftoken": "tok"}
        )

    def test_action_absoluta_sin_csrf(self) -> None:
        page = '<form action="https://h/hpsmart/refresh/hpcache"></form>'
        assert parse_cache_refresh_form(page, origin="https://o") == (
            "https://h/hpsmart/refresh/hpcache", {}
        )

    def test_sin_formulario_falla(self) -> None:
        with pytest.raises(ExternalServiceError, match="no está disponible"):
            parse_cache_refresh_form("<div/>", origin="https://o")

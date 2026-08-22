"""Parsing puro del HTML del PortalWeb de SDS (sin I/O)."""

import pytest

from src.modules.insumos.infrastructure.portal.portal_parsing import (
    DELETE_SUCCESS_MARKER,
    extract_csrf_token,
    is_delete_success,
    parse_delivery_location_contact,
)


def _detalle(nombre: str, email: str = "", telefono: str = "") -> str:
    return (
        '<html><section id="deliveryLocationDetails"><table>'
        f"<tr><th>Nombre de la persona de contacto</th><td>{nombre}</td></tr>"
        f"<tr><th>Correo electrónico de contacto</th><td>{email}</td></tr>"
        f"<tr><th>Teléfono de contacto</th><td>{telefono}</td></tr>"
        "</table></section></html>"
    )


def test_extract_csrf_token_devuelve_el_valor_del_input_oculto() -> None:
    html = '<form><input type="hidden" name="__csrftoken" value="abc123" /></form>'

    assert extract_csrf_token(html) == "abc123"


def test_extract_csrf_token_es_none_si_no_hay_formulario() -> None:
    assert extract_csrf_token("<html><body>Sesión vencida</body></html>") is None


@pytest.mark.parametrize(
    ("body", "esperado"),
    [(f"<p>{DELETE_SUCCESS_MARKER}</p>", True), ("<p>Error inesperado</p>", False)],
)
def test_is_delete_success_busca_el_marcador_literal(body: str, esperado: bool) -> None:
    assert is_delete_success(body) is esperado


def test_parse_contacto_separa_apellido_y_nombre_por_coma_y_limpia_html() -> None:
    html = _detalle("<b>P&eacute;rez, Juan</b>", "juan@x.com", "<span>11-5555</span>")

    contacto = parse_delivery_location_contact(html, 42)

    assert contacto is not None
    assert (contacto.apellido, contacto.nombre) == ("Pérez", "Juan")
    assert (contacto.email, contacto.telefono) == ("juan@x.com", "11-5555")


def test_parse_contacto_sin_coma_deja_todo_en_apellido() -> None:
    contacto = parse_delivery_location_contact(_detalle("Mesa de ayuda"), 1)

    assert contacto is not None
    assert (contacto.apellido, contacto.nombre) == ("Mesa de ayuda", "")


def test_parse_contacto_sin_nombre_es_none() -> None:
    assert parse_delivery_location_contact(_detalle("", "x@y.com"), 7) is None


def test_parse_contacto_sin_seccion_de_detalle_lanza_value_error() -> None:
    with pytest.raises(ValueError, match="Delivery location 9"):
        parse_delivery_location_contact("<html><body>otra página</body></html>", 9)

"""Tests del parseo puro de respuestas del wsAyC — casos portados de test_soap_query.py
y de las respuestas reales documentadas en la caracterización."""

from src.modules.insumos.infrastructure.soap import wsayc_parsing as parsing

# --- parse_machine ---------------------------------------------------------------------


def test_parse_machine_vacio_devuelve_none() -> None:
    """"[]" es la respuesta real cuando el equipo no está asignado a ninguna empresa."""
    assert parsing.parse_machine("[]") is None


def test_parse_machine_con_datos() -> None:
    raw = (
        '{"Machine": {"familia_id": "255", "Familia": "HP E50145/52645", '
        '"empresa_id": "8", "sucursal_id": "13840"}}'
    )
    machine = parsing.parse_machine(raw)
    assert machine is not None
    assert machine.familia_id == "255"
    assert machine.familia_name == "HP E50145/52645"
    assert machine.empresa_id == "8"
    assert machine.sucursal_id == "13840"


def test_parse_machine_sin_familia_mapea_familia_vacia() -> None:
    machine = parsing.parse_machine('{"Machine": {"empresa_id": "8"}}')
    assert machine is not None
    assert machine.familia_id == ""


# --- parse_supply_by_id ----------------------------------------------------------------


def test_parse_supply_by_id_extrae_el_supply() -> None:
    raw = (
        '{"Supply": {"id": "443017", "NroIncidenteCliente": "SDS-974325", '
        '"Estado": "Pendiente", "Fecha": "31/07/2026 10:00:00"}}'
    )
    supply = parsing.parse_supply_by_id(raw)
    assert supply is not None
    assert supply.supply_id == 443017
    assert supply.reference == "SDS-974325"
    assert supply.estado == "Pendiente"


def test_parse_supply_by_id_vacio_devuelve_none() -> None:
    assert parsing.parse_supply_by_id("[]") is None


def test_parse_supply_by_id_basura_devuelve_none() -> None:
    assert parsing.parse_supply_by_id("<html>error</html>") is None


# --- parse_top_supplies ----------------------------------------------------------------


def test_parse_top_supplies_extrae_lista_y_parsea_id_con_check_digit() -> None:
    raw = (
        '[{"Supply": {"IdSupply": "441415-9", "Estado": "Pendiente", '
        '"NroSerieSolicitud": "SERIE1"}}]'
    )
    supplies = parsing.parse_top_supplies(raw)
    assert len(supplies) == 1
    assert supplies[0].supply_id == 441415  # sin el check digit
    assert supplies[0].nro_serie_solicitud == "SERIE1"


def test_parse_top_supplies_no_lista_devuelve_vacio() -> None:
    assert parsing.parse_top_supplies("[]") == []
    assert parsing.parse_top_supplies(None) == []
    assert parsing.parse_top_supplies("basura") == []


# --- parse_article_parts ---------------------------------------------------------------


def test_parse_article_parts_normaliza_lista_a_dict() -> None:
    """El SOAP devuelve [{"id","name"}] — se normaliza al {id: nombre} que espera
    insumo_matching (misma forma que devolvía el portal)."""
    raw = '[{"id":"3729","name":"HP E50145/52645 - Toner"}]'
    assert parsing.parse_article_parts(raw) == {"3729": "HP E50145/52645 - Toner"}


def test_parse_article_parts_sin_datos_devuelve_vacio() -> None:
    assert parsing.parse_article_parts("[]") == {}
    assert parsing.parse_article_parts('{"error": "x"}') == {}


# --- parse_persist_response ------------------------------------------------------------


def test_parse_persist_response_id_valido() -> None:
    assert parsing.parse_persist_response('"441770"') == 441770


def test_parse_persist_response_cero_o_basura_devuelve_cero() -> None:
    assert parsing.parse_persist_response("0") == 0
    assert parsing.parse_persist_response('"0"') == 0
    assert parsing.parse_persist_response("no-json") == 0
    assert parsing.parse_persist_response(None) == 0


# --- parse_details_description ---------------------------------------------------------


def test_parse_details_description_toma_el_primer_detail() -> None:
    raw = '[{"Detail": {"Insumo": "HP E50145/52645 - Toner"}}]'
    assert parsing.parse_details_description(raw) == "HP E50145/52645 - Toner"


def test_parse_details_description_sin_items_devuelve_vacio() -> None:
    assert parsing.parse_details_description("[]") == ""
    assert parsing.parse_details_description(None) == ""


# --- contactos del prefill (getSupplyById) ---------------------------------------------


def test_supply_from_dict_mapea_contactos_con_strip() -> None:
    supply = parsing.supply_from_dict(
        {
            "id": "1",
            "Solicitante": "  Juan Gomez ",
            "TelefonoSolicitante": "1140004000",
            "EmailSolicitante": "sol@e.com",
            "EntregaA": "Ana Perez",
            "TelefonoDestinatario": "1150005000",
            "EmailDestinatario": "dest@e.com",
        }
    )
    assert supply.solicitante_nombre == "Juan Gomez"
    assert supply.destinatario_nombre == "Ana Perez"

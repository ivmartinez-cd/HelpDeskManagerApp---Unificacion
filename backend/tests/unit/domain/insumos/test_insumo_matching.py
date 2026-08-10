"""Tests de caracterización de la heurística de selección de insumo.

Portados 1:1 del legacy (`tests/test_insumo_matching.py` de SDSInsumos-develop) — son los
mismos casos reales; solo cambia la firma (InsumoQuery agrupa el contexto) y que los
errores ahora son de dominio (FamiliaSinInsumosError en vez de RuntimeError).
"""

import pytest

from src.modules.insumos.domain.errors import FamiliaSinInsumosError, InsumoAmbiguoError
from src.modules.insumos.domain.services.insumo_matching import InsumoQuery, select_insumo_id


def _query(
    familia_name: str = "Toner",
    device_serial: str = "SERIE1",
    requested_sku: str = "",
    description: str = "",
    override_insumo_id: str | None = None,
) -> InsumoQuery:
    return InsumoQuery(
        familia_name=familia_name,
        device_serial=device_serial,
        requested_sku=requested_sku,
        description=description,
        override_insumo_id=override_insumo_id,
    )


def test_sku_exact_match() -> None:
    options = {
        "101": {"sku": "CF230A", "nombre": "Toner HP 30A Negro"},
        "102": {"sku": "CF231A", "nombre": "Toner HP 31A Negro"},
    }
    assert select_insumo_id(options, _query(requested_sku="CF230A")) == "101"


def test_single_option_fallback() -> None:
    options = {"201": "Toner HP 30A"}
    assert select_insumo_id(options, _query()) == "201"


def test_color_match_yellow() -> None:
    options = {"301": "Yellow Toner", "302": "Black Toner"}
    assert select_insumo_id(options, _query(description="Cartucho amarillo HP 414A")) == "301"


def test_color_match_black() -> None:
    options = {"301": "Yellow Toner", "302": "Black Toner"}
    assert select_insumo_id(options, _query(description="Cartucho negro HP 414A")) == "302"


def test_color_match_cyan() -> None:
    options = {"301": "Cyan Toner", "302": "Black Toner"}
    assert select_insumo_id(options, _query(description="Toner cian HP")) == "301"


def test_drum_type_filter() -> None:
    options = {"401": "Drum Unit Black", "402": "Yellow Toner"}
    assert select_insumo_id(options, _query("Drum", description="Tambor negro HP")) == "401"


def test_drum_not_confused_with_toner() -> None:
    """Un drum black no debe resolver como toner black aunque compartan 'black' en el nombre."""
    options = {"401": "Drum Unit Black", "402": "Black Toner"}
    # desc contiene "tambor" → tipo drum → solo "Drum Unit Black" candidato
    result = select_insumo_id(options, _query("Drum", description="Tambor negro HP LaserJet"))
    assert result == "401"


def test_cmy_fallback() -> None:
    """Si la desc pide un color no-negro y hay una sola opción CMY, usarla."""
    options = {"501": "CMY Drum Unit", "502": "Black Drum Unit"}
    assert select_insumo_id(options, _query("Drum", description="Tambor cian HP")) == "501"


def test_empty_options_raises() -> None:
    with pytest.raises(FamiliaSinInsumosError, match="No hay insumos"):
        select_insumo_id({}, _query())


def test_multiple_no_match_raises() -> None:
    options = {"601": "Option A", "602": "Option B"}
    with pytest.raises(InsumoAmbiguoError, match="múltiples insumos") as exc_info:
        select_insumo_id(options, _query())
    assert exc_info.value.options == [
        {"id": "601", "name": "Option A"},
        {"id": "602", "name": "Option B"},
    ]


def test_color_ambiguous_raises_with_options() -> None:
    """Caso real (solicitud 970568): dos insumos Cyan de distinta capacidad para el mismo color."""
    options = {
        "4882": {"nombre": "HP T850/T950 - Cyan 130ml (738)"},
        "4709": {"nombre": "HP T850/T950 - Cyan 300ml"},
    }
    query = _query(
        familia_name="HP T850/T950 - Plotter",
        device_serial="CN4766M07W",
        requested_sku="498M7A",
        description="Cyan Ink Cartridge",
    )
    with pytest.raises(InsumoAmbiguoError, match="múltiples insumos candidatos") as exc_info:
        select_insumo_id(options, query)
    assert exc_info.value.options == [
        {"id": "4882", "name": "HP T850/T950 - Cyan 130ml (738)"},
        {"id": "4709", "name": "HP T850/T950 - Cyan 300ml"},
    ]


def test_override_skips_search() -> None:
    """override_insumo_id (elección manual del operador) evita la búsqueda automática —
    ni siquiera mira `options` (acá vacío a propósito, para probar que no la usa)."""
    query = _query(
        familia_name="HP T850/T950 - Plotter",
        device_serial="CN4766M07W",
        requested_sku="498M7A",
        description="Cyan Ink Cartridge",
        override_insumo_id="4709",
    )
    assert select_insumo_id({}, query) == "4709"


def test_color_match_cuando_el_nombre_de_la_opcion_esta_en_espanol() -> None:
    """Caso real (familia 203, Samsung SL-X4300LX vía SOAP): a diferencia del resto de
    las opciones HP/Samsung, esta trae el color en español ("Negro") en vez de en inglés
    ("Black") en el propio nombre de la opción de Canal Directo."""
    options = {
        "2966": "Developer Samsung CLX-9201 /SL-X4300 /HP E77830 - Yellow",
        "2967": "Developer Samsung CLX-9201 /SL-X4300 /HP E77830 - Magenta",
        "2968": "Developer Samsung CLX-9201 /SL-X4300 /HP E77830 - Cyan",
        "2969": "Developer Samsung CLX-9201 /SL-X4300 /HP E77830 - Negro",
    }
    result = select_insumo_id(
        options, _query("Samsung SL-X4300LX", description="Developer negro")
    )
    assert result == "2969"


def test_waste_type_filter() -> None:
    options = {"701": "Waste Toner Collection", "702": "Black Toner"}
    assert select_insumo_id(options, _query("Waste", description="Unidad de recogida")) == "701"

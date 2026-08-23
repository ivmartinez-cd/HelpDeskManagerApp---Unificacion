from src.modules.preventivos.domain.services.geocoding import (
    armar_direccion,
    elegir_automatico,
    normalizar_domicilio,
)
from src.shared.domain.repositories.geocoding_gateway import GeocodeCandidato


def _candidato(**overrides: object) -> GeocodeCandidato:
    base: dict[str, object] = dict(
        formatted_address="Av. Siempre Viva 742, Springfield",
        latitud=-31.5,
        longitud=-68.5,
        location_type="ROOFTOP",
        tipos=(),
        partial_match=False,
    )
    base.update(overrides)
    return GeocodeCandidato(**base)  # type: ignore[arg-type]


def test_normalizar_domicilio_saca_sufijo_de_piso_y_altura_cero() -> None:
    assert normalizar_domicilio("San Isidro 2200 Piso: Dpto:") == "San Isidro 2200"
    assert normalizar_domicilio("Constituyentes 0 Piso: Dpto:") == "Constituyentes"


def test_normalizar_domicilio_vacio_queda_vacio() -> None:
    assert normalizar_domicilio("0") == ""


def test_armar_direccion_combina_domicilio_ciudad_provincia() -> None:
    direccion = armar_direccion("San Isidro 2200 Piso: Dpto:", "Mendoza", "Mendoza")
    assert direccion == "San Isidro 2200, Mendoza, Mendoza, Argentina"


def test_armar_direccion_sin_domicilio_es_none() -> None:
    assert armar_direccion("", "Mendoza", "Mendoza") is None
    assert armar_direccion("0", "Mendoza", "Mendoza") is None


def test_elegir_automatico_candidato_unico_rooftop() -> None:
    assert elegir_automatico([_candidato()]) is not None


def test_elegir_automatico_varios_candidatos_es_ambiguo() -> None:
    assert elegir_automatico([_candidato(), _candidato()]) is None


def test_elegir_automatico_partial_match_no_se_autoresuelve() -> None:
    assert elegir_automatico([_candidato(partial_match=True)]) is None


def test_elegir_automatico_route_no_se_autoresuelve() -> None:
    candidato = _candidato(location_type="GEOMETRIC_CENTER", tipos=("route",))
    assert elegir_automatico([candidato]) is None


def test_elegir_automatico_intersection_se_autoresuelve() -> None:
    candidato = _candidato(location_type="GEOMETRIC_CENTER", tipos=("intersection",))
    assert elegir_automatico([candidato]) is candidato


def test_elegir_automatico_sin_precision_ni_interseccion_es_ambiguo() -> None:
    assert elegir_automatico([_candidato(location_type="APPROXIMATE")]) is None

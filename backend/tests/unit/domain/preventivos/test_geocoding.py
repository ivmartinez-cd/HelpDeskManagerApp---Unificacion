from src.modules.preventivos.domain.services.geocoding import (
    agrupar_referencias_por_ciudad,
    armar_direccion,
    clave_ubicacion,
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


def test_elegir_automatico_caba_con_candidato_en_conurbano_es_ambiguo() -> None:
    # Caso real (auditoría 2026-08-23): "Chile 1347" con ciudad=CABA
    # devolvió un único candidato ROOFTOP en Valentín Alsina (Conurbano).
    candidato = _candidato(
        formatted_address="Chile 1347, B1868 Valentín Alsina, Provincia de Buenos Aires, Argentina"
    )
    assert elegir_automatico([candidato], "CABA") is None


def test_elegir_automatico_caba_con_candidato_en_caba_se_autoresuelve() -> None:
    candidato = _candidato(
        formatted_address="Av. Rivadavia 789, C1002AAF Cdad. Autónoma de Buenos Aires, Argentina"
    )
    assert elegir_automatico([candidato], "CABA") is candidato


def test_elegir_automatico_caba_acepta_variantes_de_ciudad() -> None:
    candidato = _candidato(
        formatted_address="Av. Rivadavia 789, C1002AAF Cdad. Autónoma de Buenos Aires, Argentina"
    )
    assert elegir_automatico([candidato], "Capital Federal") is candidato
    assert elegir_automatico([candidato], "Ciudad Autonoma de Buenos Aires") is candidato


def test_elegir_automatico_ciudad_no_caba_sin_referencias_no_se_valida() -> None:
    # Sin referencias geográficas (el caller no las pasó, o hay menos de
    # _MIN_REFERENCIAS) no hay con qué juzgar geometría — no se rechaza.
    candidato = _candidato(formatted_address="Cualquier lugar, Mendoza, Argentina")
    assert elegir_automatico([candidato], "Mendoza") is candidato


def test_elegir_automatico_lejos_de_las_referencias_es_ambiguo() -> None:
    # Caso real (barrido 2026-08-23): "Belgrano 664, Garín" devolvió un
    # único candidato ROOFTOP en "Cno. Gral. Belgrano" — a 35km de las otras
    # sucursales confiables de Garín.
    candidato = _candidato(latitud=-34.6886, longitud=-58.3774)
    referencias = tuple((-34.42 + i * 0.001, -58.72 + i * 0.001) for i in range(5))
    assert elegir_automatico([candidato], "Garin", referencias) is None


def test_elegir_automatico_cerca_de_las_referencias_se_autoresuelve() -> None:
    candidato = _candidato(latitud=-34.4195, longitud=-58.7286)
    referencias = tuple((-34.42 + i * 0.001, -58.72 + i * 0.001) for i in range(5))
    assert elegir_automatico([candidato], "Garin", referencias) is candidato


def test_elegir_automatico_referencias_insuficientes_no_se_valida() -> None:
    # Menos de _MIN_REFERENCIAS: no hay muestra suficiente para un centroide
    # confiable, no se rechaza por esto.
    candidato = _candidato(latitud=-34.6886, longitud=-58.3774)
    referencias = ((-34.42, -58.72), (-34.421, -58.721))
    assert elegir_automatico([candidato], "Garin", referencias) is candidato


def test_elegir_automatico_caba_no_usa_referencias_geometricas() -> None:
    # CABA sigue validándose solo por texto — geometría no aplica ahí
    # (demasiado grande/diversa para un centroide único, ver auditoría).
    candidato = _candidato(
        formatted_address="Av. Rivadavia 789, C1002AAF Cdad. Autónoma de Buenos Aires, Argentina",
        latitud=-40.0,
        longitud=-70.0,
    )
    referencias = tuple((-34.6 + i * 0.001, -58.4 + i * 0.001) for i in range(5))
    assert elegir_automatico([candidato], "CABA", referencias) is candidato


def test_clave_ubicacion_normaliza_acentos_mayusculas_y_espacios() -> None:
    assert clave_ubicacion("  Garín ", "Buenos Aires") == clave_ubicacion("GARIN", "buenos aires")


def test_agrupar_referencias_por_ciudad_agrupa_por_clave() -> None:
    entradas = [
        ("Garin", "Buenos Aires", -34.42, -58.72),
        ("GARIN", "buenos aires", -34.421, -58.721),
        ("Pilar", "Buenos Aires", -34.45, -58.91),
    ]
    agrupadas = agrupar_referencias_por_ciudad(entradas)
    assert agrupadas[clave_ubicacion("Garin", "Buenos Aires")] == [
        (-34.42, -58.72),
        (-34.421, -58.721),
    ]
    assert agrupadas[clave_ubicacion("Pilar", "Buenos Aires")] == [(-34.45, -58.91)]


def test_agrupar_referencias_por_ciudad_excluye_caba() -> None:
    entradas = [("CABA", "Capital Federal", -34.6, -58.4)]
    assert agrupar_referencias_por_ciudad(entradas) == {}

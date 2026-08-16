"""Normalización de direcciones Siges, elección de candidato y haversine.

Fixtures tomadas de datos reales del muestreo de calidad 2026-08-15 (incluida
la rural del caso BAHIA→Las Horquetas: "Ruta Nacional 33 KM 167, GUAMINI")."""

import pytest

from src.modules.liquidaciones.domain.repositories.geocoding_gateway import GeocodeCandidato
from src.modules.liquidaciones.domain.services.geolocalizacion import (
    UMBRAL_PIN_SOSPECHOSO_KM,
    armar_direccion,
    elegir_automatico,
    es_pin_sospechoso,
    haversine_km,
    normalizar_domicilio,
)


def _candidato(
    location_type: str = "ROOFTOP",
    tipos: tuple[str, ...] = ("street_address",),
    partial_match: bool = False,
) -> GeocodeCandidato:
    return GeocodeCandidato(
        formatted_address="Av. Callao 1337, CABA, Argentina",
        latitud=-34.593456,
        longitud=-58.392671,
        location_type=location_type,
        tipos=tipos,
        partial_match=partial_match,
    )


class TestNormalizarDomicilio:
    def test_saca_sufijo_piso_dpto_vacio(self) -> None:
        assert normalizar_domicilio("Avenida Callao 1337 Piso: Dpto:") == "Avenida Callao 1337"

    def test_saca_sufijo_piso_con_dato(self) -> None:
        resultado = normalizar_domicilio("Alférez Hipólito Bouchard 4191 Piso:7 Dpto:")
        assert resultado == "Alférez Hipólito Bouchard 4191"

    def test_saca_altura_cero_final(self) -> None:
        assert normalizar_domicilio("Av. Gaona y Victorica 0") == "Av. Gaona y Victorica"

    def test_conserva_km_de_ruta(self) -> None:
        assert normalizar_domicilio("Ruta 70 Km 74") == "Ruta 70 Km 74"

    def test_rural_con_altura_cero_y_piso(self) -> None:
        resultado = normalizar_domicilio("Mitre y Gral. Acha S/N 0 Piso: Dpto:")
        assert resultado == "Mitre y Gral. Acha S/N"


class TestArmarDireccion:
    def test_completa(self) -> None:
        assert armar_direccion("Ruta Nacional 33 KM 167", "GUAMINI", "Buenos Aires") == (
            "Ruta Nacional 33 KM 167, GUAMINI, Buenos Aires, Argentina"
        )

    def test_sin_provincia(self) -> None:
        assert armar_direccion("Conesa 4261", "CABA", None) == "Conesa 4261, CABA, Argentina"

    def test_solo_localidad(self) -> None:
        assert armar_direccion(None, "Carhué", "Buenos Aires") == (
            "Carhué, Buenos Aires, Argentina"
        )

    def test_sin_domicilio_ni_localidad(self) -> None:
        assert armar_direccion(None, "  ", "Buenos Aires") is None

    def test_domicilio_que_normaliza_a_vacio(self) -> None:
        assert armar_direccion(" 0", None, "Santa Fe") is None


class TestElegirAutomatico:
    def test_unico_rooftop_se_elige(self) -> None:
        candidato = _candidato()
        assert elegir_automatico([candidato]) is candidato

    def test_unico_range_interpolated_se_elige(self) -> None:
        candidato = _candidato(location_type="RANGE_INTERPOLATED")
        assert elegir_automatico([candidato]) is candidato

    def test_interseccion_exacta_se_elige(self) -> None:
        candidato = _candidato(location_type="GEOMETRIC_CENTER", tipos=("intersection",))
        assert elegir_automatico([candidato]) is candidato

    def test_centro_de_ruta_no_se_elige(self) -> None:
        # Caso real: "Ruta Nacional 33 KM 167, GUAMINI" devuelve el centro
        # geométrico de la RN33 entera, a ~110 km del pin verdadero.
        rn33 = GeocodeCandidato(
            formatted_address="RN33, Argentina",
            latitud=-36.0252331,
            longitud=-62.7410169,
            location_type="GEOMETRIC_CENTER",
            tipos=("route",),
        )
        assert elegir_automatico([rn33]) is None

    def test_partial_match_no_se_elige(self) -> None:
        assert elegir_automatico([_candidato(partial_match=True)]) is None

    def test_varios_candidatos_no_se_elige(self) -> None:
        assert elegir_automatico([_candidato(), _candidato()]) is None

    def test_sin_candidatos(self) -> None:
        assert elegir_automatico([]) is None


class TestHaversine:
    def test_mismo_punto_es_cero(self) -> None:
        assert haversine_km(-34.6, -58.4, -34.6, -58.4) == 0.0

    def test_un_grado_de_latitud(self) -> None:
        assert haversine_km(0.0, 0.0, 1.0, 0.0) == pytest.approx(111.19, abs=0.1)

    def test_base_bahia_a_pin_guamini(self) -> None:
        # Distancia en línea recta base BAHIA → pin Siges de Las Horquetas;
        # la ruta real por RN33 da 199,294 km (dato de tabla_kms).
        recta = haversine_km(-38.7189846, -62.264305, -37.0222087, -62.3782513)
        assert recta == pytest.approx(189.0, abs=1.0)

    def test_umbral_sospechoso(self) -> None:
        assert not es_pin_sospechoso(UMBRAL_PIN_SOSPECHOSO_KM)
        assert es_pin_sospechoso(UMBRAL_PIN_SOSPECHOSO_KM + 0.01)

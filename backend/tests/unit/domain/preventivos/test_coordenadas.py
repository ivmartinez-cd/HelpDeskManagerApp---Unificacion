from src.modules.preventivos.domain.services.coordenadas import (
    coordenada_reconciliada,
    coordenada_valida,
    haversine_km,
)


def test_coordenada_dentro_de_argentina_es_valida() -> None:
    assert coordenada_valida(-34.603722, -58.381592) is True


def test_coordenada_none_es_invalida() -> None:
    assert coordenada_valida(None, -58.4) is False
    assert coordenada_valida(-34.6, None) is False


def test_coordenada_en_cero_es_invalida() -> None:
    # Placeholder de carga conocido en Siges (79 de 4835 sucursales medidas).
    assert coordenada_valida(0, 0) is False


def test_coordenada_fuera_del_bbox_argentino_es_invalida() -> None:
    # Ejemplo real medido en Siges: 36.778261 / -119.417932 (California).
    assert coordenada_valida(36.778261, -119.417932) is False


def test_longitud_sin_punto_decimal_es_invalida() -> None:
    # Ejemplo real medido en Siges: falta el punto (-58.750875 -> -58750875).
    assert coordenada_valida(-34.380142999, -58750875.0) is False


def test_haversine_de_un_punto_a_si_mismo_es_cero() -> None:
    assert haversine_km(-34.6037, -58.3816, -34.6037, -58.3816) == 0


def test_haversine_caba_a_cordoba_da_el_orden_de_magnitud_correcto() -> None:
    # Distancia real aprox. CABA-Córdoba: ~650 km.
    dist = haversine_km(-34.6037, -58.3816, -31.4201, -64.1888)
    assert 640 <= dist <= 660


def test_coordenada_reconciliada_cuando_siges_cae_cerca_del_override() -> None:
    # Caso real (2026-08-23): Fort Music, override vs. Siges corregido a
    # pocos metros de distancia.
    assert coordenada_reconciliada(-34.6145828, -58.4195644, -34.6146, -58.4196) is True


def test_coordenada_no_reconciliada_si_siges_sigue_lejos() -> None:
    assert coordenada_reconciliada(-34.6145828, -58.4195644, -34.6178908, -58.5301257) is False


def test_coordenada_no_reconciliada_si_siges_sigue_invalida() -> None:
    assert coordenada_reconciliada(-34.6145828, -58.4195644, 0, 0) is False
    assert coordenada_reconciliada(-34.6145828, -58.4195644, None, None) is False

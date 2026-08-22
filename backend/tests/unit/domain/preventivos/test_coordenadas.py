from src.modules.preventivos.domain.services.coordenadas import coordenada_valida


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

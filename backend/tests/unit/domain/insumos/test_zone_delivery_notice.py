"""Tests de zone_delivery_notice.detect_sucursal_override.

Casos reales y adversos del patrón "CARGAR PARA SUCURSAL: <nombre>" en la observación
de una zona (ver zone_delivery_notice.py para el contexto de negocio — Arcadium Lithium
es el cliente testigo). Portados 1:1 del legacy SDSInsumos (mismos casos reales)."""

from src.modules.insumos.domain.services.zone_delivery_notice import detect_sucursal_override


def test_texto_exacto_arcadium() -> None:
    texto = "CARGAR PARA SUCURSAL: OFICINA SALTA (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "OFICINA SALTA"
    assert result.observacion == texto


def test_minuscula() -> None:
    texto = "cargar para sucursal: oficina salta (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "oficina salta"


def test_sin_dos_puntos() -> None:
    texto = "CARGAR PARA SUCURSAL OFICINA SALTA (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "OFICINA SALTA"


def test_con_espacios_multiples() -> None:
    texto = "CARGAR   PARA  SUCURSAL:    OFICINA SALTA (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "OFICINA SALTA"


def test_con_acentos_en_el_disparador() -> None:
    # Typo con acento en "sucúrsal" — tiene que matchear igual.
    texto = "CARGÁR PARA SUCÚRSAL: OFICINA SALTA (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "OFICINA SALTA"


def test_disparador_en_otra_posicion_de_la_frase() -> None:
    texto = "Atención — CARGAR PARA SUCURSAL: PLANTA FENIX. Avisar antes de ir."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "PLANTA FENIX"


def test_orden_de_palabras_invertido_para_cargar() -> None:
    # No hay formato fijo: "sucursal" + un verbo de despacho, en cualquier orden.
    texto = "PARA CARGAR EN SUCURSAL OFICINA SALTA (no despachar a la mina)."
    result = detect_sucursal_override(texto)
    assert result.requiere_cambio is True
    assert result.sucursal == "OFICINA SALTA"


def test_verbo_despachar_en_vez_de_cargar() -> None:
    result = detect_sucursal_override("Despachar en sucursal: Oficina Salta (no a la mina).")
    assert result.requiere_cambio is True
    assert result.sucursal == "Oficina Salta"


def test_verbo_entregar() -> None:
    result = detect_sucursal_override("Entregar en sucursal Oficina Salta.")
    assert result.requiere_cambio is True
    assert result.sucursal == "Oficina Salta"


def test_match_sin_sucursal_parseable_avisa_igual() -> None:
    # El patrón matchea pero no queda texto legible después — se avisa igual con la
    # observación completa, nunca se descarta el aviso por no poder parsear.
    result = detect_sucursal_override("Instrucción especial: CARGAR PARA SUCURSAL")
    assert result.requiere_cambio is True
    assert result.sucursal is None
    assert result.observacion == "Instrucción especial: CARGAR PARA SUCURSAL"


def test_observacion_que_no_debe_disparar() -> None:
    result = detect_sucursal_override("Contactar al depósito antes de las 10hs.")
    assert result.requiere_cambio is False
    assert result.sucursal is None


def test_observacion_sucursal_sin_relacion_no_dispara() -> None:
    # "sucursal" aparece pero no como parte del patrón "cargar para sucursal".
    result = detect_sucursal_override("La sucursal permanece cerrada los feriados.")
    assert result.requiere_cambio is False
    assert result.sucursal is None


def test_campo_vacio() -> None:
    result = detect_sucursal_override("")
    assert result.requiere_cambio is False
    assert result.sucursal is None
    assert result.observacion == ""


def test_campo_none() -> None:
    result = detect_sucursal_override(None)
    assert result.requiere_cambio is False
    assert result.sucursal is None


def test_campo_solo_espacios() -> None:
    result = detect_sucursal_override("   ")
    assert result.requiere_cambio is False
    assert result.sucursal is None


def test_sucursal_con_coma_y_texto_adicional_no_se_corta_de_mas() -> None:
    # Sin paréntesis/punto de corte, se queda con el resto de la línea tal cual (menos
    # confiar en heurísticas de puntuación que puedan comerse un nombre legítimo).
    result = detect_sucursal_override("CARGAR PARA SUCURSAL: PLANTA GUEMES, avisar al sereno")
    assert result.requiere_cambio is True
    assert result.sucursal == "PLANTA GUEMES, avisar al sereno"

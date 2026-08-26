from datetime import date

from src.modules.preventivos.domain.services.vencimiento import calcular_vencimiento

_HOY = date(2026, 8, 14)


def test_sin_frecuencia_none_no_inventa_fecha() -> None:
    resultado = calcular_vencimiento(date(2026, 1, 1), None, _HOY)

    assert resultado.estado == "sin_frecuencia"
    assert resultado.proximo_vencimiento is None
    assert resultado.dias_vencido is None


def test_frecuencia_cero_es_sin_frecuencia() -> None:
    # Sucursal.TipoPreventivo=0 en Siges = "sin preventivo pactado" (Dias=0).
    resultado = calcular_vencimiento(date(2026, 1, 1), 0, _HOY)

    assert resultado.estado == "sin_frecuencia"
    assert resultado.proximo_vencimiento is None


def test_sin_preventivo_previo_no_inventa_fecha() -> None:
    resultado = calcular_vencimiento(None, 180, _HOY)

    assert resultado.estado == "sin_preventivo"
    assert resultado.proximo_vencimiento is None
    assert resultado.dias_vencido is None


def test_sin_preventivo_con_instalacion_calcula_fecha_tentativa() -> None:
    # Caso real (Cepas Argentinas, MXBC179G54): instalación 2026-04-20 +
    # frecuencia 180 = tentativa 2026-10-17, pero el estado sigue siendo
    # sin_preventivo — nunca se "inventa" un al_dia/vencido a partir de esto.
    resultado = calcular_vencimiento(
        None, 180, _HOY, fecha_instalacion=date(2026, 4, 20)
    )

    assert resultado.estado == "sin_preventivo"
    assert resultado.proximo_vencimiento is None
    assert resultado.fecha_tentativa == date(2026, 10, 17)


def test_sin_preventivo_sin_instalacion_no_tiene_fecha_tentativa() -> None:
    resultado = calcular_vencimiento(None, 180, _HOY)

    assert resultado.fecha_tentativa is None


def test_sin_frecuencia_no_calcula_tentativa_aunque_haya_instalacion() -> None:
    resultado = calcular_vencimiento(None, None, _HOY, fecha_instalacion=date(2026, 4, 20))

    assert resultado.estado == "sin_frecuencia"
    assert resultado.fecha_tentativa is None


def test_sin_frecuencia_gana_sobre_sin_preventivo() -> None:
    resultado = calcular_vencimiento(None, None, _HOY)

    assert resultado.estado == "sin_frecuencia"


def test_vencido_calcula_dias_de_atraso() -> None:
    # Último preventivo 2026-01-01 + 180 días = 2026-06-30 -> 45 días vencido.
    resultado = calcular_vencimiento(date(2026, 1, 1), 180, _HOY)

    assert resultado.estado == "vencido"
    assert resultado.proximo_vencimiento == date(2026, 6, 30)
    assert resultado.dias_vencido == 45


def test_vence_hoy_no_esta_vencido_sino_por_vencer() -> None:
    resultado = calcular_vencimiento(date(2026, 2, 15), 180, _HOY)

    assert resultado.proximo_vencimiento == _HOY
    assert resultado.estado == "por_vencer"
    assert resultado.dias_vencido is None


def test_por_vencer_dentro_del_umbral() -> None:
    resultado = calcular_vencimiento(date(2026, 3, 1), 180, _HOY)

    assert resultado.estado == "por_vencer"
    assert resultado.proximo_vencimiento == date(2026, 8, 28)


def test_al_dia_fuera_del_umbral() -> None:
    resultado = calcular_vencimiento(date(2026, 8, 1), 180, _HOY)

    assert resultado.estado == "al_dia"
    assert resultado.proximo_vencimiento == date(2027, 1, 28)


def test_limite_exacto_del_umbral_es_por_vencer() -> None:
    # proximo == hoy + 30 días exactos.
    resultado = calcular_vencimiento(date(2026, 3, 17), 180, _HOY, umbral_por_vencer_dias=30)

    assert resultado.proximo_vencimiento == date(2026, 9, 13)
    assert resultado.estado == "por_vencer"


def test_fecha_de_ultimo_preventivo_futura_no_rompe() -> None:
    # Anomalía de datos (fecha cargada a futuro en Siges): se calcula igual,
    # queda al día — nunca una excepción.
    resultado = calcular_vencimiento(date(2026, 9, 1), 180, _HOY)

    assert resultado.estado == "al_dia"
    assert resultado.proximo_vencimiento == date(2027, 2, 28)

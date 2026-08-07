"""Mismos escenarios que HelpDeskManager-Web/backend/tests/test_proyeccion.py y
test_proyeccion_caracterizacion.py — deben dar los mismos resultados acá.
Ver CONTADORES_CARACTERIZACION.md para el detalle de cada caso."""

from datetime import date

from src.modules.contadores.domain.services.counter_projector import project_device_counter
from src.modules.contadores.domain.value_objects.counter_reading import CounterReading
from src.modules.contadores.domain.value_objects.device_projection_input import (
    DeviceProjectionInput,
)
from src.modules.contadores.domain.value_objects.projection_settings import ProjectionSettings

_DEFAULT_SETTINGS = ProjectionSettings()


def _device(readings: list[tuple[str, int, str]], fecha_toma: date) -> DeviceProjectionInput:
    return DeviceProjectionInput(
        serie="SER", clase="Mono", articulo="X", sector="A",
        readings=[CounterReading(date.fromisoformat(f), c, t) for f, c, t in readings],
        fecha_toma=fecha_toma,
    )


def test_exact_match_on_fecha_toma_is_real() -> None:
    device = _device(
        [("2026-03-01", 50000, "Lectura"), ("2026-05-15", 55000, "Lectura")],
        date(2026, 5, 15),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.metodo == "REAL"
    assert result.contador_proyectado == 55000


def test_basic_trend_projection() -> None:
    # Igual que test_proyeccion.py::test_ejecutar_proyeccion_basica, serie B:
    # 30000 -> 33000 en 30 dias hasta 01/04, proyectado 44 dias hasta 15/05.
    device = _device(
        [("2026-02-01", 30000, "Lectura"), ("2026-03-01", 31500, "Lectura"),
         ("2026-04-01", 33000, "Lectura")],
        date(2026, 5, 15),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.metodo == "PROYECTADO"
    assert round(result.consumo_diario_promedio, 4) == 50.9793
    assert result.dias_proyectados == 44
    assert result.contador_proyectado == 35243


def test_reset_flagged_by_tipo_contador() -> None:
    device = _device(
        [("2026-01-01", 90000, "Lectura"), ("2026-01-10", 0, "Reiniciar Contador"),
         ("2026-01-20", 1000, "Lectura")],
        date(2026, 1, 30),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.metodo == "PROYECTADO"
    assert result.consumo_diario_promedio == 100.0
    assert result.contador_proyectado == 2000


def test_reset_detected_by_counter_drop_without_flag() -> None:
    device = _device(
        [("2026-01-01", 50000, "Lectura"), ("2026-01-10", 500, "Lectura"),
         ("2026-01-20", 1500, "Lectura")],
        date(2026, 1, 30),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    # Base de la proyección = ultima lectura conocida (1500), no el punto de
    # reset (500): 1500 + 100/dia * 10 dias = 2500 (verificado contra la app vieja).
    assert result.contador_proyectado == 2500
    assert result.consumo_diario_promedio == 100.0


def test_umbral_minimo_consumo_forces_zero() -> None:
    device = _device(
        [("2026-01-01", 1000, "Lectura"), ("2026-01-11", 1001, "Lectura")],
        date(2026, 1, 21),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.consumo_diario_promedio == 0.0
    assert result.contador_proyectado == 1001


def test_max_antiguedad_lectura_forces_zero_consumption() -> None:
    settings = ProjectionSettings(ventana_reciente_dias=3650, max_antiguedad_lectura_dias=365)
    device = _device(
        [("2025-01-01", 1000, "Lectura"), ("2025-02-01", 4000, "Lectura")],
        date(2026, 6, 1),
    )
    result, _ = project_device_counter(device, settings)
    assert result.consumo_diario_promedio == 0.0
    assert result.contador_proyectado == 4000


def test_tolerance_uses_last_reading_as_real_without_projecting() -> None:
    device = _device(
        [("2026-01-01", 1000, "Lectura"), ("2026-01-18", 5000, "Lectura")],
        date(2026, 1, 20),
    )
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.metodo == "REAL"
    assert result.contador_proyectado == 5000
    assert result.dias_proyectados == 0


def test_sin_datos_when_only_future_readings_exist() -> None:
    device = _device([("2026-02-15", 1000, "Lectura")], date(2026, 1, 1))
    result, _ = project_device_counter(device, _DEFAULT_SETTINGS)
    assert result.metodo == "SIN_DATOS"
    assert result.contador_proyectado is None


def test_ventana_reciente_discards_old_high_rate_interval() -> None:
    settings = ProjectionSettings(ventana_reciente_dias=30, max_antiguedad_lectura_dias=3650)
    device = _device(
        [("2025-01-01", 0, "Lectura"), ("2025-02-01", 30000, "Lectura"),
         ("2026-01-01", 100000, "Lectura"), ("2026-01-11", 100100, "Lectura")],
        date(2026, 1, 21),
    )
    result, _ = project_device_counter(device, settings)
    assert result.consumo_diario_promedio == 10.0
    assert result.contador_proyectado == 100200

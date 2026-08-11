"""Tests de validate_settings — los rangos que protegen al auto-loader real."""

from dataclasses import replace

from src.modules.insumos.domain.services.settings_validation import validate_settings
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

VALIDOS = InsumosSettings()


def _con(**overrides: object) -> InsumosSettings:
    return replace(VALIDOS, **overrides)  # type: ignore[arg-type]


def test_los_defaults_de_fabrica_son_validos() -> None:
    assert validate_settings(VALIDOS, []) is None


def test_los_umbrales_tienen_que_ir_de_mas_urgente_a_menos() -> None:
    assert validate_settings(_con(threshold_critical=7, threshold_urgent=7), []) == (
        "El umbral Crítico debe ser menor que Urgente."
    )
    assert validate_settings(_con(threshold_urgent=14, threshold_warning=14), []) == (
        "El umbral Urgente debe ser menor que Atención."
    )


def test_el_tope_de_dias_de_autocarga_acota_el_dano_de_un_cambio_de_config() -> None:
    """Sin este tope, un `autoloadMaxDays` alto vuelve elegible casi toda la cola
    pendiente y el auto-loader crea esos pedidos de verdad."""
    assert validate_settings(_con(autoload_max_days=31), []) is not None
    assert validate_settings(_con(autoload_max_days=0), []) is not None
    assert validate_settings(_con(autoload_max_days=30), []) is None


def test_la_ventana_de_validacion_no_puede_quedar_en_cero_ni_ser_eterna() -> None:
    assert validate_settings(_con(validation_window_hours=0), []) is not None
    assert validate_settings(_con(validation_window_hours=49), []) is not None
    assert validate_settings(_con(validation_window_hours=1), []) is None


def test_el_horario_laboral_tiene_que_empezar_antes_de_terminar() -> None:
    error = validate_settings(_con(alert_work_hour_start=18, alert_work_hour_end=18), [])

    assert error == "La hora de inicio debe ser menor que la hora de fin."


def test_hora_de_inicio_y_fin_dentro_del_dia() -> None:
    assert validate_settings(_con(alert_work_hour_start=24), []) is not None
    assert validate_settings(_con(alert_work_hour_end=25), []) is not None


def test_limites_de_deteccion_de_caida_masiva() -> None:
    assert validate_settings(_con(offline_outage_min_devices=1), []) is not None
    assert validate_settings(_con(offline_outage_min_percent=0), []) is not None
    assert validate_settings(_con(offline_device_hours=23), []) is not None
    assert validate_settings(_con(offline_monitor_hours=721), []) is not None


def test_los_mails_de_logistica_se_validan_y_el_error_los_nombra() -> None:
    error = validate_settings(VALIDOS, ["ok@example.com", "roto", "otro@mal"])

    assert error == "Email(s) inválido(s) en logística: roto, otro@mal"


def test_sin_destinatarios_de_logistica_no_hay_error() -> None:
    assert validate_settings(VALIDOS, []) is None


def test_se_reporta_el_primer_problema_encontrado_no_todos() -> None:
    """El formulario del legacy muestra un solo mensaje por vez; el orden de los
    chequeos es parte del contrato."""
    error = validate_settings(
        _con(threshold_critical=99, autoload_max_days=999), ["roto"]
    )

    assert error == "El umbral Crítico debe ser menor que Urgente."

"""Tests de validate_settings — los rangos que protegen al auto-loader real."""

from dataclasses import replace

from src.modules.insumos.domain.services.settings_validation import validate_settings
from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

VALIDOS = InsumosSettings()
# Destinatario de alertas técnicas válido y no vacío, para no confundir los
# tests que ejercitan otras validaciones con el error nuevo de "requerido".
OPS_OK = ["ops@example.com"]


def _con(**overrides: object) -> InsumosSettings:
    return replace(VALIDOS, **overrides)  # type: ignore[arg-type]


def test_los_defaults_de_fabrica_son_validos() -> None:
    assert validate_settings(VALIDOS, [], OPS_OK) is None


def test_los_umbrales_tienen_que_ir_de_mas_urgente_a_menos() -> None:
    assert validate_settings(_con(threshold_critical=7, threshold_urgent=7), [], OPS_OK) == (
        "El umbral Crítico debe ser menor que Urgente."
    )
    assert validate_settings(_con(threshold_urgent=14, threshold_warning=14), [], OPS_OK) == (
        "El umbral Urgente debe ser menor que Atención."
    )


def test_el_tope_de_dias_de_autocarga_acota_el_dano_de_un_cambio_de_config() -> None:
    """Sin este tope, un `autoloadMaxDays` alto vuelve elegible casi toda la cola
    pendiente y el auto-loader crea esos pedidos de verdad."""
    assert validate_settings(_con(autoload_max_days=31), [], OPS_OK) is not None
    assert validate_settings(_con(autoload_max_days=0), [], OPS_OK) is not None
    assert validate_settings(_con(autoload_max_days=30), [], OPS_OK) is None


def test_la_ventana_de_validacion_no_puede_quedar_en_cero_ni_ser_eterna() -> None:
    assert validate_settings(_con(validation_window_hours=0), [], OPS_OK) is not None
    assert validate_settings(_con(validation_window_hours=49), [], OPS_OK) is not None
    assert validate_settings(_con(validation_window_hours=1), [], OPS_OK) is None


def test_el_horario_laboral_tiene_que_empezar_antes_de_terminar() -> None:
    error = validate_settings(_con(alert_work_hour_start=18, alert_work_hour_end=18), [], OPS_OK)

    assert error == "La hora de inicio debe ser menor que la hora de fin."


def test_hora_de_inicio_y_fin_dentro_del_dia() -> None:
    assert validate_settings(_con(alert_work_hour_start=24), [], OPS_OK) is not None
    assert validate_settings(_con(alert_work_hour_end=25), [], OPS_OK) is not None


def test_limites_de_deteccion_de_caida_masiva() -> None:
    assert validate_settings(_con(offline_outage_min_devices=1), [], OPS_OK) is not None
    assert validate_settings(_con(offline_outage_min_percent=0), [], OPS_OK) is not None
    assert validate_settings(_con(offline_device_hours=23), [], OPS_OK) is not None
    assert validate_settings(_con(offline_monitor_hours=721), [], OPS_OK) is not None


def test_los_mails_de_logistica_se_validan_y_el_error_los_nombra() -> None:
    error = validate_settings(VALIDOS, ["ok@example.com", "roto", "otro@mal"], OPS_OK)

    assert error == "Email(s) inválido(s) en logística: roto, otro@mal"


def test_sin_destinatarios_de_logistica_no_hay_error() -> None:
    """Logística sí puede quedar vacía: "no se envían avisos" es una
    configuración válida (a diferencia de las alertas técnicas)."""
    assert validate_settings(VALIDOS, [], OPS_OK) is None


def test_sin_destinatarios_de_alertas_tecnicas_hay_error() -> None:
    """A diferencia de logística, este campo nunca puede quedar vacío — sin un
    destinatario, una falla real del sistema no le llega a nadie. Resguardo
    directo del incidente real del 2026-08-12 (ver CLAUDE.md)."""
    error = validate_settings(VALIDOS, [], [])

    assert error == (
        "Tiene que haber al menos un email de alertas técnicas (poller caído/recuperado)."
    )


def test_los_mails_de_alertas_tecnicas_se_validan_y_el_error_los_nombra() -> None:
    error = validate_settings(VALIDOS, [], ["ok@example.com", "roto"])

    assert error == "Email(s) inválido(s) en alertas técnicas: roto"


def test_se_reporta_el_primer_problema_encontrado_no_todos() -> None:
    """El formulario del legacy muestra un solo mensaje por vez; el orden de los
    chequeos es parte del contrato."""
    error = validate_settings(
        _con(threshold_critical=99, autoload_max_days=999), ["roto"], OPS_OK
    )

    assert error == "El umbral Crítico debe ser menor que Urgente."

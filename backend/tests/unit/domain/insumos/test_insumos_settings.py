"""Tests del tipado/defaults de settings (port de api_helpers.get_settings)."""

from src.modules.insumos.domain.value_objects.insumos_settings import settings_from_raw


def test_sin_datos_usa_todos_los_defaults() -> None:
    settings = settings_from_raw({})
    assert settings.threshold_critical == 3
    assert settings.threshold_urgent == 7
    assert settings.threshold_warning == 14
    assert settings.autoload_enabled is False
    assert settings.validation_window_hours == 6
    assert settings.alert_work_hours_enabled is True


def test_valores_de_db_pisan_los_defaults() -> None:
    settings = settings_from_raw(
        {"threshold_critical": "5", "autoload_enabled": "1", "logistics_mail_to": "log@e.com"}
    )
    assert settings.threshold_critical == 5
    assert settings.autoload_enabled is True
    assert settings.logistics_mail_to == "log@e.com"


def test_valor_corrupto_usa_el_default() -> None:
    settings = settings_from_raw({"threshold_urgent": "no-un-numero"})
    assert settings.threshold_urgent == 7

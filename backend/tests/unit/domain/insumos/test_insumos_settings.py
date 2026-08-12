"""Tests del tipado/defaults de settings (port de api_helpers.get_settings)."""

from src.modules.insumos.domain.value_objects.insumos_settings import (
    logistics_recipients,
    ops_alert_recipients,
    settings_from_raw,
    settings_to_raw,
)


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


def test_ops_alert_mail_to_sin_key_en_db_usa_el_default_no_vacio() -> None:
    """A diferencia de logistics_mail_to (default ""), un ambiente sin esta key
    en app_settings todavía tiene que poder avisar una falla real. Resguardo
    directo del incidente real del 2026-08-12 (ver CLAUDE.md)."""
    settings = settings_from_raw({})

    assert settings.ops_alert_mail_to == "imartinez@canaldirecto.com.ar"
    assert ops_alert_recipients(settings) == ["imartinez@canaldirecto.com.ar"]


def test_ops_alert_mail_to_en_db_pisa_el_default() -> None:
    settings = settings_from_raw({"ops_alert_mail_to": "otro@canaldirecto.com.ar"})

    assert ops_alert_recipients(settings) == ["otro@canaldirecto.com.ar"]


def test_logistics_y_ops_alert_son_listas_independientes() -> None:
    """El bug real: los dos helpers tienen que leer keys distintas, siempre —
    una alerta técnica NUNCA debe poder terminar en logistics_recipients."""
    settings = settings_from_raw(
        {
            "logistics_mail_to": "jpcorigliano@canaldirecto.com.ar,mvillegas@canaldirecto.com.ar",
            "ops_alert_mail_to": "imartinez@canaldirecto.com.ar",
        }
    )

    assert logistics_recipients(settings) == [
        "jpcorigliano@canaldirecto.com.ar",
        "mvillegas@canaldirecto.com.ar",
    ]
    assert ops_alert_recipients(settings) == ["imartinez@canaldirecto.com.ar"]
    assert set(logistics_recipients(settings)).isdisjoint(ops_alert_recipients(settings))


def test_settings_to_raw_incluye_ops_alert_mail_to() -> None:
    settings = settings_from_raw({"ops_alert_mail_to": "a@b.com,c@d.com"})

    raw = settings_to_raw(settings)

    assert raw["ops_alert_mail_to"] == "a@b.com,c@d.com"

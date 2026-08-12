"""Settings de negocio del módulo (tabla app_settings) — port de _DEFAULT_SETTINGS y
get_settings de api_helpers.py: defaults del legacy, valores corruptos usan el default."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InsumosSettings:
    threshold_critical: int = 3
    threshold_urgent: int = 7
    threshold_warning: int = 14
    autoload_enabled: bool = False
    autoload_max_days: int = 3
    autoload_min_percent: int = 15
    # Techo de la ventana de validación 0% — 6hs: el antecedente real (CN4766M07W,
    # ago-2026) tardó ~3hs en autocorregirse.
    validation_window_hours: int = 6
    stale_device_days: int = 5
    offline_device_hours: int = 72
    offline_monitor_hours: int = 48
    offline_outage_min_devices: int = 5
    offline_outage_min_percent: int = 10
    alert_escalation_minutes: int = 60
    alert_work_hours_enabled: bool = True
    alert_work_hour_start: int = 8
    alert_work_hour_end: int = 18
    logistics_mail_to: str = ""
    # Separado a propósito de logistics_mail_to: eso es negocio (avisos de
    # despacho para logística), esto es técnico (el poller de fondo dejó de
    # responder / se recuperó) — nunca deben ir a la misma bandeja. Default
    # no vacío para que un ambiente recién levantado nunca pierda este aviso
    # en silencio. Incidente real 2026-08-12 (ver CLAUDE.md, "Modo test
    # obligatorio"): una alerta de falla del poller salió a logistics_mail_to.
    ops_alert_mail_to: str = "imartinez@canaldirecto.com.ar"


_INT_KEYS = (
    "threshold_critical",
    "threshold_urgent",
    "threshold_warning",
    "autoload_max_days",
    "autoload_min_percent",
    "validation_window_hours",
    "stale_device_days",
    "offline_device_hours",
    "offline_monitor_hours",
    "offline_outage_min_devices",
    "offline_outage_min_percent",
    "alert_escalation_minutes",
    "alert_work_hour_start",
    "alert_work_hour_end",
)


def settings_from_raw(raw: Mapping[str, str]) -> InsumosSettings:
    defaults = InsumosSettings()
    ints: dict[str, int] = {}
    for key in _INT_KEYS:
        try:
            ints[key] = int(raw[key])
        except KeyError:
            ints[key] = getattr(defaults, key)
        except (ValueError, TypeError):
            logger.warning("Setting inválido %s=%r, usando default", key, raw.get(key))
            ints[key] = getattr(defaults, key)
    return InsumosSettings(
        autoload_enabled=raw.get("autoload_enabled", "0") == "1",
        alert_work_hours_enabled=raw.get("alert_work_hours_enabled", "1") == "1",
        logistics_mail_to=raw.get("logistics_mail_to", ""),
        # A diferencia de logistics_mail_to (vacío = "no se envían avisos" es
        # una configuración válida), acá el ausente cae en el default de
        # negocio, no en "": un ambiente sin esta key en app_settings todavía
        # tiene que poder avisar una falla real.
        ops_alert_mail_to=raw.get("ops_alert_mail_to", defaults.ops_alert_mail_to),
        **ints,
    )


def settings_to_raw(settings: InsumosSettings) -> dict[str, str]:
    """Inversa de settings_from_raw — app_settings es key-value de strings."""
    raw = {key: str(getattr(settings, key)) for key in _INT_KEYS}
    raw["autoload_enabled"] = "1" if settings.autoload_enabled else "0"
    raw["alert_work_hours_enabled"] = "1" if settings.alert_work_hours_enabled else "0"
    raw["logistics_mail_to"] = settings.logistics_mail_to
    raw["ops_alert_mail_to"] = settings.ops_alert_mail_to
    return raw


def logistics_recipients(settings: InsumosSettings) -> list[str]:
    """La lista de destinatarios se guarda como CSV en una sola key; el valor vacío
    tiene que dar [] y no [""]."""
    return [email for email in settings.logistics_mail_to.split(",") if email]


def ops_alert_recipients(settings: InsumosSettings) -> list[str]:
    """Destinatarios de las alertas técnicas (poller caído/recuperado) — ver
    el comentario de `ops_alert_mail_to` en InsumosSettings. NUNCA usar
    logistics_recipients() para esto."""
    return [email for email in settings.ops_alert_mail_to.split(",") if email]

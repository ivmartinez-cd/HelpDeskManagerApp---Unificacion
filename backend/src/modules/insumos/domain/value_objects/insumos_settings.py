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
        **ints,
    )

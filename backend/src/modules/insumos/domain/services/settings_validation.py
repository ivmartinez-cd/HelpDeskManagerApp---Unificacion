"""Validación de los parámetros de operación antes de persistirlos (PUT /config).

Port literal de las validaciones encadenadas de routers/config.py, incluidos los
mensajes en español que ve el operador. Los rangos NO son cosméticos:

- Los topes de auto-carga acotan el daño de un cambio de configuración: sin ellos un
  `autoloadMaxDays` alto vuelve "elegible" casi toda la cola pendiente de todos los
  clientes habilitados y el auto-loader real crea esos pedidos (hallazgo #2 de
  SEGURIDAD_PENDIENTE.md del legacy). 30 días es el margen operativo más amplio que
  tuvo sentido en producción.
- El mínimo de 1h de la ventana de validación evita dejarla en 0 por error (nunca
  daría margen para que un glitch de lectura se autocorrija); 48h es el techo para no
  dejar una solicitud real indefinidamente sin cargar.

Devuelve el mensaje del primer problema encontrado, o None si está todo bien — el
endpoint responde 200 con ok=false, igual que el legacy.
"""

import re
from collections.abc import Iterable

from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_HOURS_IN_MONTH = 24 * 30
_MINUTES_IN_DAY = 24 * 60


def validate_settings(settings: InsumosSettings, logistics_emails: Iterable[str]) -> str | None:
    checks = (
        _validate_thresholds(settings),
        _validate_autoload(settings),
        _validate_offline(settings),
        _validate_alerts(settings),
        _validate_emails(logistics_emails),
    )
    return next((error for error in checks if error is not None), None)


def _validate_thresholds(settings: InsumosSettings) -> str | None:
    if settings.threshold_critical >= settings.threshold_urgent:
        return "El umbral Crítico debe ser menor que Urgente."
    if settings.threshold_urgent >= settings.threshold_warning:
        return "El umbral Urgente debe ser menor que Atención."
    return None


def _validate_autoload(settings: InsumosSettings) -> str | None:
    if not 1 <= settings.autoload_max_days <= 30:
        return "Los días para auto-carga deben estar entre 1 y 30."
    if not 1 <= settings.autoload_min_percent <= 100:
        return "El porcentaje para auto-carga debe estar entre 1 y 100."
    if not 1 <= settings.validation_window_hours <= 48:
        return "Las horas de la ventana de validación deben estar entre 1 y 48."
    return None


def _validate_offline(settings: InsumosSettings) -> str | None:
    if not 1 <= settings.stale_device_days <= 60:
        return "Los días sin contacto para marcar offline deben estar entre 1 y 60."
    if not 24 <= settings.offline_device_hours <= _HOURS_IN_MONTH:
        return (
            "Las horas sin contacto para auditar equipos offline deben estar entre 24 y 720."
        )
    if not 24 <= settings.offline_monitor_hours <= _HOURS_IN_MONTH:
        return (
            "Las horas sin contacto para considerar colector caído deben estar entre "
            "24 y 720."
        )
    if not 2 <= settings.offline_outage_min_devices <= 100:
        return (
            "El mínimo de equipos para detectar una caída masiva debe estar entre 2 y 100."
        )
    if not 1 <= settings.offline_outage_min_percent <= 100:
        return (
            "El porcentaje mínimo para detectar una caída masiva debe estar entre 1 y 100."
        )
    return None


def _validate_alerts(settings: InsumosSettings) -> str | None:
    if not 5 <= settings.alert_escalation_minutes <= _MINUTES_IN_DAY:
        return (
            "Los minutos para escalar una alerta de pedido sin cargar deben estar entre "
            "5 y 1440."
        )
    if not 0 <= settings.alert_work_hour_start < 24:
        return "La hora de inicio de horario laboral debe estar entre 0 y 23."
    if not 1 <= settings.alert_work_hour_end <= 24:
        return "La hora de fin de horario laboral debe estar entre 1 y 24."
    if settings.alert_work_hour_start >= settings.alert_work_hour_end:
        return "La hora de inicio debe ser menor que la hora de fin."
    return None


def _validate_emails(logistics_emails: Iterable[str]) -> str | None:
    invalid = [email for email in logistics_emails if not _EMAIL_RE.match(email)]
    if invalid:
        return f"Email(s) inválido(s) en logística: {', '.join(invalid)}"
    return None

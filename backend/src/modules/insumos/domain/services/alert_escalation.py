"""Cuándo corresponde escalar una alerta de solicitud sin cargar.

Con horario laboral activado no se escala nada fuera de él: escalar un sábado a las
3 de la mañana solo produce un banner que nadie puede atender y que ya está escalado
cuando alguien llega el lunes. El umbral se mide contra `requested_at` (cuándo lo pidió
HP), no contra el primer avistaje: lo que importa es hace cuánto espera el cliente.
"""

from datetime import datetime, timedelta

from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings

_SATURDAY = 5


def is_escalation_window(now_local: datetime, settings: InsumosSettings) -> bool:
    """`now_local` tiene que venir ya convertida a la zona horaria de la operación —
    esta función no hace conversión de huso."""
    if not settings.alert_work_hours_enabled:
        return True
    if now_local.weekday() >= _SATURDAY:
        return False
    return settings.alert_work_hour_start <= now_local.hour < settings.alert_work_hour_end


def escalation_cutoff(now_utc: datetime, settings: InsumosSettings) -> datetime:
    """Toda TRIGGERED con `requested_at` anterior o igual a este instante venció."""
    return now_utc - timedelta(minutes=settings.alert_escalation_minutes)

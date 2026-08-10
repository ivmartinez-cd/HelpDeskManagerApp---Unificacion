"""Clasificación de severidad de una solicitud para la UI — port de
report.status_for_days_left. Ojo: la clave del nivel "urgente" es "serious" (no
"urgent") — el frontend legacy matchea ese string, no renombrarla."""

from src.modules.insumos.domain.value_objects.insumos_settings import InsumosSettings


def status_for_days_left(days_left: int, settings: InsumosSettings) -> tuple[str, str]:
    """(statusKey, etiqueta visible) según los umbrales configurados."""
    if days_left <= settings.threshold_critical:
        return "critical", "Crítico"
    if days_left <= settings.threshold_urgent:
        return "serious", "Urgente"
    if days_left <= settings.threshold_warning:
        return "warning", "Atención"
    return "good", "OK"

"""Ventanas de "sin contacto" de un equipo, derivadas de sus alertas AVAILABILITY en
Insight — port de device_availability.py del legacy.

Insight no tiene un endpoint de historial de conectividad — lo más cercano son las
alertas AVAILABILITY en /api/devices/{id}/alerts/history: "Device busy/unavailable for
over N hours" cuando detecta que el equipo dejó de responder (recién tras confirmar N
horas sin respuesta, no en el momento real de la caída) y "Monitoring resumed" cuando
vuelve. Es justo lo que arma la franja "sin contacto" del gráfico de nivel en el portal
HP — confirmado a mano contra un caso real (equipo CN4766M07W, 18 al 29 de enero 2026).
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.modules.insumos.domain.repositories.insight_gateway import JsonDict

_ACTUAL_HOURS_RE = re.compile(r"actual\s*=\s*(\d+)\s*hrs?", re.IGNORECASE)
_UNAVAILABLE_PREFIX = "Device busy/unavailable"
_RESUMED_PREFIX = "Monitoring resumed"


@dataclass(frozen=True)
class AvailabilityWindow:
    start: str
    end: str


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_availability_windows(alerts: list[JsonDict]) -> list[AvailabilityWindow]:
    """A partir de las alertas AVAILABILITY (en cualquier orden), arma ventanas [start, end].

    Cada racha de alertas "unavailable" consecutivas (pueden repetirse escalando: "over 72
    hours", "over a week"...) es UNA sola desconexión — se abre con la primera de la racha
    y se cierra con el próximo "Monitoring resumed". El inicio se corrige hacia atrás con
    el "actual=N hrs" de la descripción cuando está presente, para acercarse al momento
    real de la desconexión en vez de a cuándo se detectó. Una racha que nunca cierra
    (todavía offline a la fecha de corte de la consulta) no genera ventana — no se sabe
    el fin.
    """
    ordered = sorted(alerts, key=lambda a: a.get("date") or "")
    windows: list[AvailabilityWindow] = []
    streak_start: datetime | None = None

    for alert in ordered:
        description = alert.get("description") or ""
        date = alert.get("date")
        if not date:
            continue
        if description.startswith(_UNAVAILABLE_PREFIX):
            if streak_start is None:
                start = _parse_iso(date)
                match = _ACTUAL_HOURS_RE.search(description)
                if match:
                    start -= timedelta(hours=int(match.group(1)))
                streak_start = start
        elif description.startswith(_RESUMED_PREFIX) and streak_start is not None:
            end = _parse_iso(date)
            windows.append(
                AvailabilityWindow(start=streak_start.isoformat(), end=end.isoformat())
            )
            streak_start = None

    return windows

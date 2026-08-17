"""Motor de salud del equipo (degradation engine).

Port exacto del legacy. Reglas en prioridad:
  R2 — Falla post-reparación → RED
  R1 — Recurrencia (>3 en 5000 págs o 7 días) → RED
  R3 — Estabilización (10000 págs o 15 días limpio) → GREEN
  Default → YELLOW

Sutilezas (§5.6 caracterización):
- dedup por (code, event_time): los logs SDS son acumulativos.
- La ventana de páginas solo aplica con counter > 0 (con counter=0,
  latest-0 ≤ 5000 es siempre true y marcaba errores viejos como recurrentes).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

CRITICAL_SEVERITIES = {"ERROR", "CRITICAL"}
RECURRENCE_THRESHOLD = 3
RECURRENCE_PAGES = 5_000
RECURRENCE_DAYS = 7
STABLE_PAGES = 10_000
STABLE_DAYS = 15


class _TelemetryEvent(Protocol):
    code: str
    severity: str
    occurrences: int
    counter: int
    event_time: datetime


@dataclass(frozen=True)
class DeviceHealth:
    status: str  # RED | YELLOW | GREEN
    label: str
    reason: str
    recommendation: str
    triggered_rule: str | None = None


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _is_critical(ev: _TelemetryEvent) -> bool:
    return (ev.severity or "").upper() in CRITICAL_SEVERITIES


def _dedup(events: list[_TelemetryEvent]) -> list[_TelemetryEvent]:
    best: dict[tuple[str, datetime], _TelemetryEvent] = {}
    for e in events:
        key = (e.code, _aware(e.event_time))
        cur = best.get(key)
        if cur is None or (e.occurrences or 0) > (cur.occurrences or 0):
            best[key] = e
    return list(best.values())


def evaluate_device_health(
    events: list[_TelemetryEvent],
    maintenance: list[_TelemetryEvent] | None = None,
    now: datetime | None = None,
) -> DeviceHealth:
    now_aware = _aware(now) if now else datetime.now(UTC)
    events = _dedup(events)
    if not events:
        return DeviceHealth(
            "GREEN", "Sin historial",
            "No hay eventos registrados.", "Sin acciones requeridas.",
        )

    crit = [e for e in events if _is_critical(e)]
    latest_counter = max(e.counter for e in events)
    return (
        _rule_post_repair(crit, maintenance or [])
        or _rule_recurrence(crit, latest_counter, now_aware)
        or _rule_stable(crit, latest_counter, now_aware)
        or DeviceHealth(
            "YELLOW", "En observación",
            "Errores críticos recientes sin alcanzar el umbral de alerta.",
            "Monitorear la evolución del equipo.",
        )
    )


def _rule_post_repair(
    crit: list[_TelemetryEvent], maintenance: list[_TelemetryEvent]
) -> DeviceHealth | None:
    dated_maint = [m for m in maintenance if getattr(m, "changed_at", None) is not None]
    if not dated_maint:
        return None
    last_maint_dt = max(_aware(m.changed_at) for m in dated_maint)  # type: ignore[attr-defined]
    post = [e for e in crit if _aware(e.event_time) > last_maint_dt]
    if not post:
        return None
    return DeviceHealth(
        "RED", "Falla post-reparación",
        f"El error crítico {post[-1].code} reapareció tras el último mantenimiento.",
        "Enviar técnico: la reparación no resolvió la falla.",
        triggered_rule="post_repair",
    )


def _rule_recurrence(
    crit: list[_TelemetryEvent], latest_counter: int, now_aware: datetime
) -> DeviceHealth | None:
    by_code: dict[str, list[_TelemetryEvent]] = {}
    for e in crit:
        by_code.setdefault(e.code, []).append(e)

    for code, group in by_code.items():
        recent = [
            e for e in group
            if (now_aware - _aware(e.event_time)).days <= RECURRENCE_DAYS
            or (e.counter > 0 and latest_counter > 0
                and (latest_counter - e.counter) <= RECURRENCE_PAGES)
        ]
        total = sum(max(1, e.occurrences) for e in recent)
        if total > RECURRENCE_THRESHOLD:
            return DeviceHealth(
                "RED", "En degradación",
                f"El error crítico {code} se repitió {total} veces "
                f"(dentro de {RECURRENCE_PAGES:,} páginas o {RECURRENCE_DAYS} días).",
                "Se recomienda Técnico.",
                triggered_rule="recurrence",
            )
    return None


def _rule_stable(
    crit: list[_TelemetryEvent], latest_counter: int, now_aware: datetime
) -> DeviceHealth | None:
    if not crit:
        return DeviceHealth(
            "GREEN", "Estable", "Sin errores críticos.",
            "Sin acciones requeridas.", triggered_rule="stable",
        )
    last_crit = max(crit, key=lambda e: _aware(e.event_time))
    days_clean = (now_aware - _aware(last_crit.event_time)).days
    pages_clean = latest_counter - last_crit.counter
    if days_clean < STABLE_DAYS and pages_clean < STABLE_PAGES:
        return None
    return DeviceHealth(
        "GREEN", "Estable",
        f"Sin errores críticos por {pages_clean:,} páginas / {days_clean} días.",
        "Sin acciones requeridas.",
        triggered_rule="stable",
    )

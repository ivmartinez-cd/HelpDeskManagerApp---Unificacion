"""Motor de comparación de snapshots y cálculo de tendencia.

Port exacto de compare_service.py del legacy. Umbrales (§7 caracterización):
- Empeoró: ERROR nuevo, o ERROR existente +≥3 ocurrencias, o 0→>0 ERRORs,
  o total ERRORs +≥20%.
- Mejoró: desapareció ≥1 ERROR Y bajó total Y sin ERRORs nuevos.
- Estable: resto.
"""

from __future__ import annotations

from typing import Any


def _is_error(severity: str | None) -> bool:
    return (severity or "").strip().upper() == "ERROR"


def compute_diff(
    saved_incidents: list[dict[str, Any]],
    current_incidents_by_code: dict[str, Any],
) -> dict[str, Any]:
    """Diff de códigos y ocurrencias entre snapshot y análisis actual."""
    saved_by_code = {i["code"]: i for i in saved_incidents}
    current_codes = set(current_incidents_by_code.keys())
    saved_codes = set(saved_by_code.keys())

    cambios: list[dict[str, Any]] = []
    for code in saved_codes & current_codes:
        so = saved_by_code[code].get("occurrences") or 0
        co_inc = current_incidents_by_code[code]
        co = co_inc if isinstance(co_inc, int) else getattr(co_inc, "occurrences", 0)
        if so != co:
            cambios.append({
                "code": code, "saved_occurrences": so,
                "current_occurrences": co, "delta": co - so,
            })

    return {
        "codigos_nuevos": list(current_codes - saved_codes),
        "codigos_desaparecidos": list(saved_codes - current_codes),
        "cambios_ocurrencias": cambios,
    }


def _current_severity(current_by_code: dict[str, Any], code: str) -> str | None:
    inc = current_by_code.get(code)
    if inc is None:
        return None
    return inc if isinstance(inc, str) else getattr(inc, "severity", None)


def _current_occ(current_by_code: dict[str, Any], code: str) -> int:
    inc = current_by_code.get(code)
    if inc is None:
        return 0
    return inc if isinstance(inc, int) else getattr(inc, "occurrences", 0)


def _empeoro(
    saved_by_code: dict[str, dict[str, Any]],
    current_by_code: dict[str, Any],
    diff: dict[str, Any],
    total_saved_err: int,
    total_current_err: int,
) -> bool:
    for code in diff.get("codigos_nuevos") or []:
        if _is_error(_current_severity(current_by_code, code)):
            return True
    for c in diff.get("cambios_ocurrencias") or []:
        si = saved_by_code.get(c.get("code"))
        if si and _is_error(si.get("severity")) and (c.get("delta") or 0) >= 3:
            return True
    if total_saved_err == 0 and total_current_err > 0:
        return True
    return total_saved_err > 0 and total_current_err >= total_saved_err * 1.20


def _mejoro(
    saved_by_code: dict[str, dict[str, Any]],
    current_by_code: dict[str, Any],
    diff: dict[str, Any],
    total_saved_err: int,
    total_current_err: int,
) -> bool:
    errors_gone = any(
        _is_error((saved_by_code.get(code) or {}).get("severity"))
        for code in diff.get("codigos_desaparecidos") or []
    )
    no_new_err = not any(
        _is_error(_current_severity(current_by_code, code))
        for code in diff.get("codigos_nuevos") or []
    )
    return errors_gone and total_current_err < total_saved_err and no_new_err


def calculate_trend(
    saved_incidents: list[dict[str, Any]],
    current_by_code: dict[str, Any],
    diff: dict[str, Any],
) -> str:
    """'empeoro' | 'estable' | 'mejoro'."""
    saved_by_code = {i["code"]: i for i in saved_incidents}
    total_saved_err = sum(
        i.get("occurrences") or 0 for i in saved_incidents if _is_error(i.get("severity"))
    )
    total_current_err = sum(
        _current_occ(current_by_code, code)
        for code in current_by_code
        if _is_error(_current_severity(current_by_code, code))
    )
    if _empeoro(saved_by_code, current_by_code, diff, total_saved_err, total_current_err):
        return "empeoro"
    if _mejoro(saved_by_code, current_by_code, diff, total_saved_err, total_current_err):
        return "mejoro"
    return "estable"


def diff_two_snapshots(
    older_incidents: list[dict[str, Any]],
    newer_incidents: list[dict[str, Any]],
    diferencia_dias: int,
) -> dict[str, Any]:
    """Diff entre dos snapshots almacenados (sin re-parsear logs)."""

    class _Adapter:
        def __init__(self, d: dict[str, Any]) -> None:
            self.code = d.get("code", "")
            self.occurrences = d.get("occurrences") or 0
            self.severity = d.get("severity", "INFO")

    older_by_code = {i["code"]: i for i in older_incidents}
    newer_by_code = {i["code"]: i for i in newer_incidents}
    older_codes = set(older_by_code)
    newer_codes = set(newer_by_code)

    cambios: list[dict[str, Any]] = []
    for code in older_codes & newer_codes:
        so = older_by_code[code].get("occurrences") or 0
        co = newer_by_code[code].get("occurrences") or 0
        if so != co:
            cambios.append({
                "code": code, "saved_occurrences": so,
                "current_occurrences": co, "delta": co - so,
            })

    diff: dict[str, Any] = {
        "codigos_nuevos": list(newer_codes - older_codes),
        "codigos_desaparecidos": list(older_codes - newer_codes),
        "cambios_ocurrencias": cambios,
        "diferencia_dias": diferencia_dias,
    }
    current_map = {i["code"]: _Adapter(i) for i in newer_incidents}
    diff["tendencia"] = calculate_trend(older_incidents, current_map, diff)
    return diff

"""
Migración de datos: VacaSync legacy → helpdesk monorepo (módulo vacaciones).

Fuente:  /tmp/vacasync.sql  (backup de producción vacasync-20260730.sql)
Destino: helpdesk-db (tablas vacaciones_* + department compartida)

Uso:
    uv run python scripts/vacasync_migrate.py
    uv run python scripts/vacasync_migrate.py --dry-run
    uv run python scripts/vacasync_migrate.py --backup /ruta/al/backup.sql

Pre-condiciones:
    1. Alembic aplicado — todas las tablas vacaciones_* deben existir.
    2. El script es idempotente (ON CONFLICT DO NOTHING): se puede volver
       a correr sin duplicar filas.

Tablas ignoradas (sin equivalente en el nuevo schema):
    - User          → cuentas app_user se crean/vinculan por separado
    - Notification  → no existe en el nuevo schema
    - _prisma_migrations → irrelevante

Paso post-migración (impreso al final):
    Vincular vacaciones_empleado.user_id con los app_user existentes por email.
"""

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

import asyncpg

# ── Configuración ──────────────────────────────────────────────────────────────

DEFAULT_BACKUP = Path("/tmp/vacasync.sql")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://helpdesk:CHANGE_ME@db:5432/helpdesk",
)

_COPY_RE = re.compile(
    r'^COPY public\."(\w+)"\s+\(([^)]+)\)\s+FROM stdin;\n(.*?)\n\\\.', re.DOTALL | re.MULTILINE
)

# ── Parser ─────────────────────────────────────────────────────────────────────


def parse_backup(path: Path) -> dict[str, tuple[list[str], list[list[str]]]]:
    text = path.read_text(encoding="utf-8")
    result: dict[str, tuple[list[str], list[list[str]]]] = {}
    for match in _COPY_RE.finditer(text):
        table = match.group(1)
        raw_cols = match.group(2)
        raw_data = match.group(3)
        cols = [c.strip().strip('"') for c in raw_cols.split(",")]
        rows = [line.split("\t") for line in raw_data.splitlines() if line]
        result[table] = (cols, rows)
    return result


_COPY_ESCAPES = {"\\n": "\n", "\\t": "\t", "\\r": "\r", "\\\\": "\\"}
_COPY_ESCAPE_RE = re.compile(r"\\[ntr\\]")


def _unescape(v: str) -> str:
    """Des-escapa el formato COPY de pg_dump (\\n, \\t, \\r, \\\\) en una sola
    pasada — encadenar replace() procesaría dos veces los backslashes. Sin esto,
    un texto con salto de línea real llega con un "\\n" literal al destino."""
    return _COPY_ESCAPE_RE.sub(lambda m: _COPY_ESCAPES[m.group(0)], v)


def as_dict(cols: list[str], row: list[str]) -> dict[str, Any]:
    return {
        c: (None if v == r"\N" else _unescape(v)) for c, v in zip(cols, row, strict=True)
    }


# ── Conversiones de tipo ───────────────────────────────────────────────────────


def uid(s: str | None) -> uuid.UUID | None:
    return uuid.UUID(s) if s else None


def to_date(ts: str | None) -> date | None:
    """'2017-05-02 00:00:00' → date(2017, 5, 2)"""
    return date.fromisoformat(ts[:10]) if ts else None


def to_ts(ts: str | None) -> datetime | None:
    """'2026-06-29 18:59:23.611' → datetime (naive, se interpreta como UTC en asyncpg)."""
    if not ts:
        return None
    # Normalizar a 6 dígitos de microsegundos
    return datetime.fromisoformat(ts)


def to_bool(s: str | None) -> bool | None:
    if s is None:
        return None
    return s in ("t", "true", "True", "1", "TRUE")


def trunc(s: str | None, n: int) -> str | None:
    return s[:n] if s else None


def to_seniority_tiers(raw: str) -> str:
    """JSON legacy (claves camelCase minYears/maxYears/days) → snake_case
    (min_years/max_years/days), que es lo que espera SqlAlchemyConfigRepository."""
    tiers = json.loads(raw)
    return json.dumps([
        {"min_years": t["minYears"], "max_years": t["maxYears"], "days": t["days"]}
        for t in tiers
    ])


# ── Loaders ────────────────────────────────────────────────────────────────────


async def load_department(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["Department"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((uid(r["id"]), r["name"].strip(), r["color"], True))
    if conn:
        await conn.executemany(
            """
            INSERT INTO department (id, name, color, is_active)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_cargo(data: dict, conn: asyncpg.Connection | None) -> int:
    """Position + PositionOverlapLimit → vacaciones_cargo."""
    pos_cols, pos_rows = data["Position"]
    lim_cols, lim_rows = data["PositionOverlapLimit"]

    overlap: dict[str, int] = {}
    for row in lim_rows:
        r = as_dict(lim_cols, row)
        overlap[r["positionId"]] = int(r["maxEmployees"])

    records = []
    for row in pos_rows:
        r = as_dict(pos_cols, row)
        records.append((
            uid(r["id"]),
            r["name"],   # NO strip: hay "Tecnico CABA" y "Tecnico CABA " como entidades distintas
            overlap.get(r["id"]),
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_cargo (id, name, max_simultaneos, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_feriado(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["Holiday"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            r["name"],
            to_date(r["date"]),
            to_bool(r["deductsVacation"]),
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_feriado
                (id, name, date, deducts_vacation, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_config(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["SystemConfig"]
    r = as_dict(cols, rows[0])
    if conn:
        await conn.execute(
            """
            INSERT INTO vacaciones_config (
                id, seniority_tiers,
                min_advance_notice_days, max_overlap_percent, max_overlap_count,
                allow_advance_request, max_advance_days,
                next_year_open_day, next_year_open_month,
                allow_carry_over, max_carry_over_days,
                updated_at
            ) VALUES (
                'singleton', $1::jsonb,
                $2, $3, $4,
                $5, $6,
                $7, $8,
                $9, $10,
                $11
            )
            ON CONFLICT (id) DO UPDATE SET
                seniority_tiers         = EXCLUDED.seniority_tiers,
                min_advance_notice_days = EXCLUDED.min_advance_notice_days,
                max_overlap_percent     = EXCLUDED.max_overlap_percent,
                max_overlap_count       = EXCLUDED.max_overlap_count,
                allow_advance_request   = EXCLUDED.allow_advance_request,
                max_advance_days        = EXCLUDED.max_advance_days,
                next_year_open_day      = EXCLUDED.next_year_open_day,
                next_year_open_month    = EXCLUDED.next_year_open_month,
                allow_carry_over        = EXCLUDED.allow_carry_over,
                max_carry_over_days     = EXCLUDED.max_carry_over_days,
                updated_at              = EXCLUDED.updated_at
            """,
            to_seniority_tiers(r["seniorityTiers"]),
            int(r["minAdvanceNoticeDays"]),
            int(r["maxOverlapPercent"]),
            int(r["maxOverlapCount"]),
            to_bool(r["allowAdvanceRequest"]),
            int(r["maxAdvanceDays"]),
            int(r["nextYearOpenDay"]),
            int(r["nextYearOpenMonth"]),
            to_bool(r["allowCarryOver"]),
            int(r["maxCarryOverDays"]),
            to_ts(r["updatedAt"]),
        )
    return 1


async def load_empleado(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["Employee"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            r["firstName"],
            r["lastName"],
            r["email"],
            to_date(r["hireDate"]),
            int(r["annualVacationDays"]),
            r["status"],
            r["color"],
            uid(r["departmentId"]),
            uid(r["positionId"]),   # → cargo_id
            None,                   # user_id: vincular por email después
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_empleado (
                id, first_name, last_name, email,
                hire_date, annual_vacation_days, status, color,
                department_id, cargo_id, user_id,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10, $11,
                $12, $13
            )
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_ciclo(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["VacationCycle"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            uid(r["employeeId"]),
            int(r["year"]),
            int(r["annualDays"]),
            int(r["carryOver"]) if r["carryOver"] is not None else 0,
            to_bool(r["isOpen"]),
            to_ts(r.get("openedAt")),
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_ciclo (
                id, empleado_id, year, annual_days, carry_over,
                is_open, opened_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9
            )
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_solicitud(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["VacationRequest"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            uid(r["employeeId"]),
            to_date(r["startDate"]),
            to_date(r["endDate"]),
            int(r["daysRequested"]),
            int(r["chargedToYear"]) if r["chargedToYear"] is not None else None,
            trunc(r.get("reason"), 500),
            r["status"],
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_solicitud (
                id, empleado_id, start_date, end_date, days_requested,
                charged_to_year, reason, status, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10
            )
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_aprobacion(data: dict, conn: asyncpg.Connection | None) -> int:
    """approverId era User.id de vacasync → approver_user_id = NULL."""
    cols, rows = data["ApprovalHistory"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            uid(r["requestId"]),
            None,
            r["decision"],
            trunc(r.get("comment"), 500),
            to_ts(r["createdAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_aprobacion (
                id, solicitud_id, approver_user_id, decision, comment, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_ausencia(data: dict, conn: asyncpg.Connection | None) -> int:
    cols, rows = data["Absence"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            uid(r["employeeId"]),
            to_date(r["startDate"]),
            to_date(r["endDate"]),
            int(r["daysCount"]),
            to_bool(r["halfDay"]),
            r["type"],
            trunc(r.get("reason"), 500),
            r["status"],
            to_ts(r["createdAt"]),
            to_ts(r["updatedAt"]),
        ))
    if conn:
        batch = 500
        for i in range(0, len(records), batch):
            await conn.executemany(
                """
                INSERT INTO vacaciones_ausencia (
                    id, empleado_id, start_date, end_date, days_count,
                    half_day, tipo, reason, status, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9, $10, $11
                )
                ON CONFLICT DO NOTHING
                """,
                records[i : i + batch],
            )
    return len(records)


async def load_exclusion(data: dict, conn: asyncpg.Connection | None) -> int:
    """Normaliza el orden para cumplir CHECK(empleado_a_id < empleado_b_id)."""
    cols, rows = data["VacationExclusion"]
    seen: set[tuple[uuid.UUID, uuid.UUID]] = set()
    records = []
    for row in rows:
        r = as_dict(cols, row)
        a_raw, b_raw = sorted([r["employeeAId"], r["employeeBId"]])
        a, b = uid(a_raw), uid(b_raw)
        if (a, b) in seen:
            continue
        seen.add((a, b))
        records.append((uid(r["id"]), a, b, to_ts(r["createdAt"])))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_exclusion (id, empleado_a_id, empleado_b_id, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


async def load_audit_log(data: dict, conn: asyncpg.Connection | None) -> int:
    """userId de vacasync → user_id = NULL (no hay mapping a app_user)."""
    cols, rows = data["AuditLog"]
    records = []
    for row in rows:
        r = as_dict(cols, row)
        records.append((
            uid(r["id"]),
            trunc(r["action"], 30),
            trunc(r["entity"], 40),
            trunc(r.get("entityId"), 64),
            None,
            r.get("metadata"),
            to_ts(r["createdAt"]),
        ))
    if conn:
        await conn.executemany(
            """
            INSERT INTO vacaciones_audit_log (
                id, accion, entidad, entidad_id, user_id, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
            ON CONFLICT DO NOTHING
            """,
            records,
        )
    return len(records)


# ── Orden de ejecución (respeta FK) ───────────────────────────────────────────

STEPS = [
    ("Department",        "department",           load_department),
    ("Position",          "vacaciones_cargo",      load_cargo),
    ("Holiday",           "vacaciones_feriado",    load_feriado),
    ("SystemConfig",      "vacaciones_config",     load_config),
    ("Employee",          "vacaciones_empleado",   load_empleado),
    ("VacationCycle",     "vacaciones_ciclo",      load_ciclo),
    ("VacationRequest",   "vacaciones_solicitud",  load_solicitud),
    ("ApprovalHistory",   "vacaciones_aprobacion", load_aprobacion),
    ("Absence",           "vacaciones_ausencia",   load_ausencia),
    ("VacationExclusion", "vacaciones_exclusion",  load_exclusion),
    ("AuditLog",          "vacaciones_audit_log",  load_audit_log),
]


async def run(backup: Path, dry: bool) -> None:
    if not backup.exists():
        print(f"ERROR: No se encuentra el backup: {backup}", file=sys.stderr)
        sys.exit(1)

    print(f"Parseando {backup} …")
    data = parse_backup(backup)
    print(f"Tablas en el backup: {sorted(data)}\n")

    if dry:
        print("=== DRY RUN — no escribe en la DB ===\n")
        for legacy, target, fn in STEPS:
            if legacy not in data:
                print(f"  SKIP  {legacy}")
                continue
            n = await fn(data, None)
            print(f"  {legacy:25s} → {target:30s}  {n:5d} filas")
        return

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        async with conn.transaction():
            for legacy, target, fn in STEPS:
                if legacy not in data:
                    print(f"  SKIP  {legacy}")
                    continue
                n = await fn(data, conn)
                print(f"  {legacy:25s} → {target:30s}  {n:5d} filas  OK")
        print("\nMigración completada. Commit aplicado.")
    except Exception:
        print("\nERROR — rollback aplicado.", file=sys.stderr)
        raise
    finally:
        await conn.close()

    print(
        "\nPaso manual pendiente — vincular empleados con sus cuentas app_user:"
        "\n"
        "\n  UPDATE vacaciones_empleado e"
        "\n  SET    user_id = u.id"
        "\n  FROM   app_user u"
        "\n  WHERE  u.email = e.email"
        "\n    AND  e.user_id IS NULL;"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup", default=str(DEFAULT_BACKUP))
    args = parser.parse_args()
    asyncio.run(run(Path(args.backup), args.dry_run))


if __name__ == "__main__":
    main()

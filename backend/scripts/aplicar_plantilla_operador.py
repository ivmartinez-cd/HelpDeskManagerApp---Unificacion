"""Concede a usuarios los grants de la plantilla "Operador" (ADR-029).

Uso (dentro del contenedor del backend):

    uv run python scripts/aplicar_plantilla_operador.py --dry-run --todos-los-operadores
    uv run python scripts/aplicar_plantilla_operador.py --todos-los-operadores
    uv run python scripts/aplicar_plantilla_operador.py ltorres@canaldirecto.com.ar ...

`--todos-los-operadores` = todos los usuarios activos que no son superadmin.
Idempotente: los grants ya existentes no se tocan; solo se auditan (`grant`,
sin actor) los que se insertan. No revoca nada: es "sumar la plantilla", no
"reemplazar por la plantilla" (para eso está la grilla de /admin).

La lista de pares es espejo de `frontend/.../permission-templates.ts`
(plantilla "Operador"). Si cambia allá, cambiar acá. Los pares que el catálogo
no declare se saltean con aviso, nunca fallan por FK.

Script operativo fuera de las capas (mismo criterio que create_admin.py).
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models import AppUser
from src.modules.auth.infrastructure.models.permission_models import (
    ModuleAction,
    PermissionAudit,
    PermissionGrant,
)
from src.shared.infrastructure.database.session import get_sessionmaker

PLANTILLA_OPERADOR: tuple[tuple[str, str], ...] = (
    ("contadores", "view"),
    ("contadores", "export"),
    ("insumos", "view"),
    ("insumos", "create"),
    ("insumos", "update"),
    ("sla", "view"),
    ("sla", "update"),
    ("prestadores", "view"),
    # Sin liquidaciones: decisión del usuario 2026-08-21 (ni consulta).
    ("preventivos", "view"),
    ("preventivos", "update"),
    ("analisis-log-hp", "view"),
    ("turnos", "view"),
    ("vacaciones", "view"),
    ("vacaciones", "create"),
    # WhatsApp sin responder (módulo wati, ae5de3e): consulta para todos los operadores.
    ("wati", "view"),
)


@dataclass(frozen=True, slots=True)
class Opciones:
    emails: list[str]
    todos_los_operadores: bool
    dry_run: bool


def _parse_args(argv: list[str]) -> Opciones:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("emails", nargs="*", help="emails de los usuarios destino")
    parser.add_argument("--todos-los-operadores", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="solo mostrar, no escribir")
    args = parser.parse_args(argv)
    if not args.emails and not args.todos_los_operadores:
        parser.error("indicá emails o --todos-los-operadores")
    return Opciones(
        emails=[e.strip().lower() for e in args.emails],
        todos_los_operadores=args.todos_los_operadores,
        dry_run=args.dry_run,
    )


async def _usuarios_destino(session: AsyncSession, opciones: Opciones) -> list[AppUser]:
    stmt = select(AppUser).where(AppUser.is_active.is_(True))
    if opciones.todos_los_operadores:
        stmt = stmt.where(AppUser.is_superadmin.is_(False))
    else:
        stmt = stmt.where(AppUser.email.in_(opciones.emails))
    usuarios = list((await session.execute(stmt.order_by(AppUser.email))).scalars())
    faltantes = set(opciones.emails) - {u.email for u in usuarios}
    for email in sorted(faltantes):
        print(f"AVISO: {email} no existe o está inactivo; se saltea", file=sys.stderr)
    return usuarios


async def _pares_validos(session: AsyncSession) -> list[tuple[str, str]]:
    rows = (await session.execute(select(ModuleAction.module_key, ModuleAction.action_key))).all()
    catalogo = {(m, a) for m, a in rows}
    validos = [p for p in PLANTILLA_OPERADOR if p in catalogo]
    for par in PLANTILLA_OPERADOR:
        if par not in catalogo:
            print(f"AVISO: {par[0]}.{par[1]} no está en el catálogo; se saltea", file=sys.stderr)
    return validos


async def _conceder(session: AsyncSession, user: AppUser, pares: list[tuple[str, str]]) -> int:
    filas = [{"user_id": user.id, "module_key": m, "action_key": a} for m, a in pares]
    stmt = (
        pg_insert(PermissionGrant)
        .values(filas)
        .on_conflict_do_nothing()
        .returning(PermissionGrant.module_key, PermissionGrant.action_key)
    )
    nuevos = (await session.execute(stmt)).all()
    session.add_all(
        PermissionAudit(
            actor_user_id=None,
            target_user_id=user.id,
            module_key=m,
            action_key=a,
            operation="grant",
        )
        for m, a in nuevos
    )
    return len(nuevos)


async def _run(opciones: Opciones) -> None:
    async with get_sessionmaker()() as session:
        usuarios = await _usuarios_destino(session, opciones)
        pares = await _pares_validos(session)
        print(f"Plantilla Operador: {len(pares)} pares; destino: {len(usuarios)} usuario(s)")
        for user in usuarios:
            nuevos = await _conceder(session, user, pares)
            print(f"  {user.email}: +{nuevos} grant(s) nuevos (resto ya los tenía)")
        if opciones.dry_run:
            await session.rollback()
            print("dry-run: no se escribió nada")
        else:
            await session.commit()
            print("OK: grants y auditoría guardados")


def main() -> None:
    asyncio.run(_run(_parse_args(sys.argv[1:])))


if __name__ == "__main__":
    main()

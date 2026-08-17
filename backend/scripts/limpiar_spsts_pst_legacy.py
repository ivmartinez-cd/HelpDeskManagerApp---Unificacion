"""Remediación de la deuda SPST (docs/liquidaciones/DEUDA_SPSTS_CREADOS_COMO_PST.md):
SPSTs heredados del legacy con prefijo "PST " que en Siges son PSTs, no SPSTs.

Propuesta del doc:
- Filas de Tabla KM del SPST "PST " genérico → `spst_id = NULL` (la base del PST
  padre ya rutea igual).
- Excepción pares de tilde (PENTACOM): el duplicado SIN tilde reasigna sus filas
  al SPST CON tilde (el activo real), que se conserva.
- El SPST genérico se elimina después de reasignar.

Por default corre en --dry-run (solo reporta). `--apply` ejecuta en una
transacción — NO correrlo sin el ok de la TL a las 3 preguntas abiertas del doc.

Uso (dentro del contenedor backend):
    uv run python scripts/limpiar_spsts_pst_legacy.py            # dry-run
    uv run python scripts/limpiar_spsts_pst_legacy.py --apply    # ejecuta
"""

import argparse
import asyncio
import unicodedata
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infrastructure.database.session import get_sessionmaker

_SQL_CANDIDATOS = text("""
SELECT s.id, s.nombre, s.prestador_id, p.nombre_corto AS prestador,
       (SELECT COUNT(*) FROM tabla_kms t WHERE t.spst_id = s.id) AS filas
FROM spsts s
JOIN prestadores p ON p.id = s.prestador_id
WHERE s.nombre LIKE 'PST %'
ORDER BY filas DESC, s.nombre
""")


def _sin_acentos(nombre: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn"
    )


@dataclass
class Plan:
    spst_id: UUID
    nombre: str
    prestador: str
    filas: int
    accion: str  # "conservar" | "reasignar_null" | "reasignar_a"
    destino_id: UUID | None = None
    destino_nombre: str | None = None


def _armar_plan(candidatos: list) -> list[Plan]:
    por_clave = {}
    for c in candidatos:
        por_clave.setdefault((c.prestador_id, _sin_acentos(c.nombre)), []).append(c)
    planes: list[Plan] = []
    for c in candidatos:
        par = [
            o for o in por_clave[(c.prestador_id, _sin_acentos(c.nombre))]
            if o.id != c.id
        ]
        if par and c.nombre == _sin_acentos(c.nombre):
            # Duplicado sin tilde: sus filas van al gemelo con tilde (activo real).
            planes.append(Plan(
                c.id, c.nombre, c.prestador, c.filas,
                "reasignar_a", par[0].id, par[0].nombre,
            ))
        elif par:
            # El gemelo con tilde es el SPST real: se conserva con sus filas.
            planes.append(Plan(c.id, c.nombre, c.prestador, c.filas, "conservar"))
        else:
            planes.append(Plan(c.id, c.nombre, c.prestador, c.filas, "reasignar_null"))
    return planes


def _reportar(planes: list[Plan]) -> None:
    total_filas = sum(p.filas for p in planes if p.accion != "conservar")
    a_borrar = [p for p in planes if p.accion != "conservar"]
    print(f"\n{len(planes)} SPSTs con prefijo 'PST ' — {len(a_borrar)} a borrar, "
          f"{total_filas} filas de Tabla KM a reasignar:\n")
    for p in planes:
        destino = {
            "conservar": "CONSERVAR (SPST real, gemelo con tilde)",
            "reasignar_null": "filas → spst_id NULL · borrar SPST",
            "reasignar_a": f"filas → '{p.destino_nombre}' · borrar SPST",
        }[p.accion]
        print(f"  [{p.prestador:>12}] {p.nombre:<45} {p.filas:>5} filas · {destino}")


async def _aplicar(session: AsyncSession, planes: list[Plan]) -> None:
    for p in planes:
        if p.accion == "conservar":
            continue
        destino = p.destino_id if p.accion == "reasignar_a" else None
        await session.execute(
            text("UPDATE tabla_kms SET spst_id = :destino WHERE spst_id = :origen"),
            {"destino": destino, "origen": p.spst_id},
        )
        await session.execute(
            text("DELETE FROM spsts WHERE id = :id"), {"id": p.spst_id}
        )
    await session.commit()
    print("\nAplicado y commiteado.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Ejecuta la remediación (default: solo dry-run)")
    args = parser.parse_args()

    factory = get_sessionmaker()
    async with factory() as session:
        candidatos = list((await session.execute(_SQL_CANDIDATOS)).all())
        planes = _armar_plan(candidatos)
        _reportar(planes)
        if not args.apply:
            print("\nDRY-RUN: no se modificó nada. Correr con --apply SOLO con el ok "
                  "de la TL (3 preguntas abiertas en DEUDA_SPSTS_CREADOS_COMO_PST.md).")
            return
        await _aplicar(session, planes)


if __name__ == "__main__":
    asyncio.run(main())

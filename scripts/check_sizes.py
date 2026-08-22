#!/usr/bin/env python3
"""Gate de tamaños (ARCHITECTURE_GUIDE.md §4) contra un inventario congelado.

ADR-017 (backend) y ADR-020 (frontend) aceptaron como deuda documentada lo que
excedía los límites en su momento y dejaron el límite vigente para código nuevo.
Este script hace cumplir esa segunda parte: mide con AST (backend) y `wc -l`
(frontend), compara contra `scripts/sizes-baseline.json` y falla con cualquier
caso que no esté en el inventario. Corre en `make check` (y por lo tanto en el
pre-push). Sin dependencias fuera de la stdlib.

Uso:
    python3 scripts/check_sizes.py            # verifica
    python3 scripts/check_sizes.py --update   # regenera el inventario (decisión
                                              # consciente: acompañar con ADR)
"""

from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "scripts", "sizes-baseline.json")
BACKEND_SRC = os.path.join(ROOT, "backend", "src")
FRONTEND_SRC = os.path.join(ROOT, "frontend", "src")
MAX_FUNC, MAX_CLASS, MAX_FILE = 20, 200, 300


def _backend() -> list[str]:
    out: list[str] = []
    for dp, _, files in os.walk(BACKEND_SRC):
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT)
            if "migrations/versions" in rel:
                continue
            src = open(p, encoding="utf-8").read()
            lines = src.count("\n")  # mismo criterio que `wc -l` (ADR-020)
            if lines > MAX_FILE:
                out.append(f"file {rel} ({lines})")
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    span = node.end_lineno - node.lineno + 1
                    if span > MAX_FUNC:
                        out.append(f"func {rel}::{node.name} ({span})")
                elif isinstance(node, ast.ClassDef):
                    span = node.end_lineno - node.lineno + 1
                    if span > MAX_CLASS:
                        out.append(f"class {rel}::{node.name} ({span})")
    return out


def _frontend() -> list[str]:
    out: list[str] = []
    for dp, _, files in os.walk(FRONTEND_SRC):
        for f in files:
            if not f.endswith((".ts", ".tsx")):
                continue
            p = os.path.join(dp, f)
            lines = open(p, encoding="utf-8").read().count("\n")  # como `wc -l`
            if lines > MAX_FILE:
                out.append(f"file {os.path.relpath(p, ROOT)} ({lines})")
    return out


def _key(entry: str) -> str:
    """Identidad sin el tamaño: que una función crezca de 25 a 28 no es un caso nuevo."""
    return entry.rsplit(" (", 1)[0]


def main() -> int:
    actual = sorted(_backend() + _frontend())
    if "--update" in sys.argv:
        json.dump({"limits": {"func": MAX_FUNC, "class": MAX_CLASS, "file": MAX_FILE},
                   "entries": actual}, open(BASELINE, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print(f"inventario actualizado: {len(actual)} entradas → {BASELINE}")
        return 0
    baseline = {_key(e) for e in json.load(open(BASELINE, encoding="utf-8"))["entries"]}
    nuevos = [e for e in actual if _key(e) not in baseline]
    resueltos = sorted(baseline - {_key(e) for e in actual})
    if resueltos:
        print(f"ℹ {len(resueltos)} entradas del inventario ya no exceden el límite "
              f"(se pueden sacar con --update).")
    if nuevos:
        print(f"✘ §4: {len(nuevos)} caso(s) nuevo(s) por encima del límite "
              f"(función >{MAX_FUNC}, clase >{MAX_CLASS}, archivo >{MAX_FILE}):")
        for e in nuevos:
            print(f"   {e}")
        print("   Dividir antes de commitear; el inventario congelado solo cubre la deuda "
              "previa (ADR-017/020).")
        return 1
    print(f"✔ §4 tamaños: sin casos nuevos ({len(actual)} en inventario)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Gate de tamaños (ARCHITECTURE_GUIDE.md §4) contra un inventario congelado.

ADR-017 (backend) y ADR-020 (frontend) aceptaron como deuda documentada lo que
excedía los límites en su momento y dejaron el límite vigente para código nuevo.
Este script hace cumplir esa segunda parte: mide con AST (backend) y `wc -l`
(frontend), compara contra `scripts/sizes-baseline.json` y falla con cualquier
caso que no esté en el inventario. Corre en `make check` (y por lo tanto en el
pre-push). Sin dependencias fuera de la stdlib.

Uso:
    python3 scripts/check_sizes.py              # árbol de trabajo (lo que tenés editado)
    python3 scripts/check_sizes.py --committed  # HEAD: lo que se va a pushear (make check / pre-push)
    python3 scripts/check_sizes.py --staged     # solo los archivos staged, con su contenido del index (pre-commit)
    python3 scripts/check_sizes.py --update     # regenera el inventario desde el árbol de
                                                # trabajo (decisión consciente: acompañar con ADR)

Con varias sesiones sobre el mismo checkout, el árbol de trabajo mezcla WIP ajeno: por eso
los hooks miden lo commiteado/staged y no lo que haya editado en disco.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tarfile
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(REPO, "scripts", "sizes-baseline.json")
MAX_FUNC, MAX_CLASS, MAX_FILE = 20, 200, 300


def _backend(ROOT: str) -> list[str]:
    out: list[str] = []
    for dp, _, files in os.walk(os.path.join(ROOT, "backend", "src")):
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


def _frontend(ROOT: str) -> list[str]:
    out: list[str] = []
    for dp, _, files in os.walk(os.path.join(ROOT, "frontend", "src")):
        for f in files:
            if not f.endswith((".ts", ".tsx")):
                continue
            p = os.path.join(dp, f)
            lines = open(p, encoding="utf-8").read().count("\n")  # como `wc -l`
            if lines > MAX_FILE:
                out.append(f"file {os.path.relpath(p, ROOT)} ({lines})")
    return out


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True).stdout


def _snapshot_head(dest: str) -> None:
    """Extrae backend/src y frontend/src de HEAD en `dest` (una sola llamada a git)."""
    tar_path = os.path.join(dest, "head.tar")
    with open(tar_path, "wb") as fh:
        fh.write(_git("archive", "HEAD", "backend/src", "frontend/src"))
    with tarfile.open(tar_path) as tar:
        tar.extractall(dest, filter="data")


def _snapshot_staged(dest: str) -> bool:
    """Escribe en `dest` el contenido del index de los archivos staged que importan.
    Devuelve False si no hay ninguno (nada que medir)."""
    staged = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR").decode().split()
    relevantes = [
        p for p in staged
        if (p.startswith("backend/src/") and p.endswith(".py"))
        or (p.startswith("frontend/src/") and p.endswith((".ts", ".tsx")))
    ]
    for p in relevantes:
        full = os.path.join(dest, p)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(_git("show", f":{p}"))
    return bool(relevantes)


def _medir(root: str) -> list[str]:
    return sorted(_backend(root) + _frontend(root))


def _key(entry: str) -> str:
    """Identidad sin el tamaño: que una función crezca de 25 a 28 no es un caso nuevo."""
    return entry.rsplit(" (", 1)[0]


def main() -> int:
    modo = next((a for a in ("--committed", "--staged", "--update") if a in sys.argv), "")
    if modo in ("--committed", "--staged"):
        with tempfile.TemporaryDirectory() as tmp:
            if modo == "--committed":
                _snapshot_head(tmp)
            elif not _snapshot_staged(tmp):
                print("✔ §4 tamaños: nada staged que medir")
                return 0
            return _verificar(_medir(tmp), f"{modo} " if modo == "--staged" else "")
    actual = _medir(REPO)
    if modo == "--update":
        json.dump({"limits": {"func": MAX_FUNC, "class": MAX_CLASS, "file": MAX_FILE},
                   "entries": actual}, open(BASELINE, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False)
        print(f"inventario actualizado: {len(actual)} entradas → {BASELINE}")
        return 0
    return _verificar(actual, "")


def _verificar(actual: list[str], etiqueta: str) -> int:
    baseline = {_key(e) for e in json.load(open(BASELINE, encoding="utf-8"))["entries"]}
    nuevos = [e for e in actual if _key(e) not in baseline]
    resueltos = sorted(baseline - {_key(e) for e in actual})
    if resueltos and not etiqueta:
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
    print(f"✔ §4 tamaños {etiqueta}: sin casos nuevos ({len(actual)} medidos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

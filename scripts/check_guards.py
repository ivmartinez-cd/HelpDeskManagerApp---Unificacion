#!/usr/bin/env python3
"""Gate de ARCHITECTURE_GUIDE.md §6 / §8 / §11 contra un inventario congelado.

Mide con AST (backend) y texto (frontend) lo que las auditorías venían revisando a mano:

  except      §6   `except Exception` / `except:` que no relanza, no loguea y no delega en
                   un handler (cuerpo = un solo `return self._algo(...)`).
  sql-fstring §8   `text(f"…")` / `.execute(f"…")` / concatenación de strings con SQL.
  secret      §8   literal tipo password/secret/api_key/token asignado en código.
  print       §12  `print(` en backend/src (fuera de scripts/migraciones).
  console     §12  `console.log(` en frontend/src.
  xss         §8   `dangerouslySetInnerHTML` en frontend/src.
  list-no-page §11 endpoint que devuelve `list[...]` sin `Page[T]`.
  no-authz    §8   endpoint sin require_permission/require_feature/identidad.

Lo ya aceptado (con ADR o justificación) vive en `scripts/guards-baseline.json`; cualquier caso
nuevo hace fallar el script. Mismos modos que check_sizes.py:

    python3 scripts/check_guards.py              # árbol de trabajo
    python3 scripts/check_guards.py --committed  # HEAD (make check / pre-push)
    python3 scripts/check_guards.py --staged     # archivos staged (pre-commit)
    python3 scripts/check_guards.py --update     # regenera el inventario (decisión consciente)
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(REPO, "scripts", "guards-baseline.json")

_SQL_WORDS = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|PRAGMA|FROM|WHERE)\b", re.I)
_SECRET = re.compile(r"(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}['\"]", re.I)
_AUTHZ_MARKERS = ("require_permission", "require_feature", "Identity", "get_current_identity",
                  "require_superadmin", "require_any", "current_identity")
_LOG_MARKERS = ("logger.", "logging.", "log.", "_log", "LOGGER")


def _py_files(root: str):
    for dp, _, files in os.walk(os.path.join(root, "backend", "src")):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dp, f)


def _ts_files(root: str):
    for dp, _, files in os.walk(os.path.join(root, "frontend", "src")):
        for f in files:
            if f.endswith((".ts", ".tsx")):
                yield os.path.join(dp, f)


def _is_broad(handler: ast.ExceptHandler) -> bool:
    t = handler.type
    return t is None or (isinstance(t, ast.Name) and t.id in ("Exception", "BaseException"))


def _delegates(handler: ast.ExceptHandler) -> bool:
    """Cuerpo = un solo `return [await] <handler>(…)` (método o función con nombre de
    intención, p. ej. `_handle_creation_failed`, `_aviso_fail_open`): el logging vive ahí."""
    if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Return):
        return False
    val = handler.body[0].value
    if isinstance(val, ast.Await):
        val = val.value
    return isinstance(val, ast.Call)


def _silent_except(handler: ast.ExceptHandler) -> bool:
    if any(isinstance(n, ast.Raise) for n in ast.walk(handler)):
        return False
    body = ast.unparse(handler)
    if any(m in body for m in _LOG_MARKERS):
        return False
    return not _delegates(handler)


def _sql_fstring(call: ast.Call) -> bool:
    func = ast.unparse(call.func)
    if not (func.endswith("text") or func.endswith(".execute") or func == "op.execute"):
        return False
    if not call.args:
        return False
    arg = call.args[0]
    if isinstance(arg, ast.JoinedStr):
        return True
    return isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Add, ast.Mod)) and bool(
        _SQL_WORDS.search(ast.unparse(arg))
    )


def _endpoint_entries(rel: str, node: ast.AST) -> list[str]:
    out: list[str] = []
    decs = [ast.unparse(d) for d in getattr(node, "decorator_list", [])]
    if not any(re.search(r"\.(get|post|put|patch|delete)\(", d) for d in decs):
        return out
    sig = ast.unparse(node.args)  # type: ignore[attr-defined]
    joined = " ".join(decs) + sig
    if not any(m in joined for m in _AUTHZ_MARKERS):
        out.append(f"no-authz {rel}::{node.name}")  # type: ignore[attr-defined]
    ret = ast.unparse(node.returns) if getattr(node, "returns", None) else ""  # type: ignore[attr-defined]
    if re.search(r"response_model=list\[", joined) or ret.startswith("list["):
        out.append(f"list-no-page {rel}::{node.name}")  # type: ignore[attr-defined]
    return out


def _backend(root: str) -> list[str]:
    out: list[str] = []
    for p in _py_files(root):
        rel = os.path.relpath(p, root)
        src = open(p, encoding="utf-8").read()
        es_migracion = "migrations/versions" in rel
        for i, line in enumerate(src.splitlines(), 1):
            if _SECRET.search(line) and "example" not in line.lower():
                out.append(f"secret {rel}:{i}")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and _is_broad(node) and _silent_except(node):
                out.append(f"except {rel}:{node.lineno}")
            elif isinstance(node, ast.Call):
                if _sql_fstring(node):
                    out.append(f"sql-fstring {rel}:{node.lineno}")
                if isinstance(node.func, ast.Name) and node.func.id == "print" and not es_migracion:
                    out.append(f"print {rel}:{node.lineno}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.extend(_endpoint_entries(rel, node))
    return out


def _frontend(root: str) -> list[str]:
    out: list[str] = []
    for p in _ts_files(root):
        rel = os.path.relpath(p, root)
        for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
            if "console.log(" in line:
                out.append(f"console {rel}:{i}")
            if "dangerouslySetInnerHTML" in line:
                out.append(f"xss {rel}:{i}")
            if _SECRET.search(line) and "example" not in line.lower():
                out.append(f"secret {rel}:{i}")
    return out


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True).stdout


def _snapshot_head(dest: str) -> None:
    tar_path = os.path.join(dest, "head.tar")
    with open(tar_path, "wb") as fh:
        fh.write(_git("archive", "HEAD", "backend/src", "frontend/src"))
    with tarfile.open(tar_path) as tar:
        tar.extractall(dest, filter="data")


def _snapshot_staged(dest: str) -> bool:
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
    """Identidad sin número de línea: que el archivo se edite más arriba no crea un caso nuevo."""
    kind, rest = entry.split(" ", 1)
    return f"{kind} {rest.rsplit(':', 1)[0]}" if "::" not in rest else entry


def _verificar(actual: list[str], etiqueta: str) -> int:
    from collections import Counter

    base = json.load(open(BASELINE, encoding="utf-8"))["entries"]
    permitidos = Counter(_key(e) for e in base)
    vistos: Counter[str] = Counter()
    nuevos: list[str] = []
    for e in actual:
        k = _key(e)
        vistos[k] += 1
        if vistos[k] > permitidos.get(k, 0):  # un caso más que los aceptados en ese archivo
            nuevos.append(e)
    baseline = set(permitidos)
    resueltos = sorted(baseline - set(vistos))
    if resueltos and not etiqueta:
        print(f"ℹ {len(resueltos)} entradas del inventario ya no aparecen (se pueden sacar con --update).")
    if nuevos:
        print(f"✘ §6/§8/§11: {len(nuevos)} caso(s) nuevo(s) fuera del inventario:")
        for e in nuevos:
            print(f"   {e}")
        print("   except silencioso → loguear/relanzar; SQL por f-string → parámetros; list[...] → "
              "Page[T]; endpoint sin authz → require_permission (o ADR + --update).")
        return 1
    print(f"✔ §6/§8/§11 {etiqueta}: sin casos nuevos ({len(actual)} medidos)")
    return 0


def main() -> int:
    modo = next((a for a in ("--committed", "--staged", "--update") if a in sys.argv), "")
    if modo in ("--committed", "--staged"):
        with tempfile.TemporaryDirectory() as tmp:
            if modo == "--committed":
                _snapshot_head(tmp)
            elif not _snapshot_staged(tmp):
                print("✔ §6/§8/§11: nada staged que medir")
                return 0
            return _verificar(_medir(tmp), f"{modo} " if modo == "--staged" else "")
    actual = _medir(REPO)
    if modo == "--update":
        json.dump({"entries": actual}, open(BASELINE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"inventario actualizado: {len(actual)} entradas → {BASELINE}")
        return 0
    return _verificar(actual, "")


if __name__ == "__main__":
    sys.exit(main())

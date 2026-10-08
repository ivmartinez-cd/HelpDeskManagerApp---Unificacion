# /// script
# requires-python = ">=3.12"
# dependencies = ["psycopg[binary]>=3.2"]
# ///
"""Integra a `develop` las ramas de los reportes que el superadmin pidió integrar
desde el panel (estado `integrar`). Corre en el host por cron cada minuto, con
flock para no pisarse (ver la entrada en `crontab -l`). No es Claude: solo git.

Solo mergea si entra limpio: el checkout principal en develop, la rama con un
nombre válido, y ninguno de los archivos que toca con cambios sin commitear de
otra sesión. Si algo falla, aborta el merge, devuelve el reporte a `resuelto`
con el motivo en la nota (el ícono del pie del menú lo marca). Nunca pushea
ni reinicia nada.
"""

import re
import subprocess
from datetime import UTC, datetime
from typing import Any

from _hdm_db import RAIZ, Conexion, conectar

# La rama viene de la DB: validarla antes de pasársela a git.
_RAMA_VALIDA = re.compile(r"^reporte-[0-9a-f]{8}(-[a-z0-9]+)*$")


def _ahora() -> datetime:
    return datetime.now(UTC).astimezone()  # hora local, para la nota y el log


class NoIntegrable(Exception):
    pass


def _git(*args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(RAIZ), *args], capture_output=True, text=True, check=False
    )
    if r.returncode != 0:
        raise NoIntegrable(f"git {args[0]}: {(r.stderr or r.stdout).strip()}")
    return r.stdout


def _ya_integrada(rama: str) -> bool:
    r = subprocess.run(
        ["git", "-C", str(RAIZ), "merge-base", "--is-ancestor", rama, "develop"],
        capture_output=True,
        check=False,
    )
    return r.returncode == 0


def _verificar(rama: str) -> list[str]:
    """Archivos que toca la rama, si se puede mergear sin pisar a nadie."""
    if _git("symbolic-ref", "--short", "HEAD").strip() != "develop":
        raise NoIntegrable("el checkout principal no está en develop")
    try:
        _git("rev-parse", "--verify", "--quiet", f"refs/heads/{rama}")
    except NoIntegrable:
        raise NoIntegrable(f"no existe la rama {rama}") from None
    archivos = _git("diff", "--name-only", f"develop...{rama}").split()
    sucios = (
        _git("status", "--porcelain", "--", *archivos).splitlines() if archivos else []
    )
    if sucios:
        lista = ", ".join(linea[3:] for linea in sucios)
        raise NoIntegrable(f"otra sesión tiene cambios sin commitear en: {lista}")
    return archivos


def _mergear(rama: str) -> None:
    try:
        _git("merge", "--no-edit", rama)
    except NoIntegrable:
        subprocess.run(
            ["git", "-C", str(RAIZ), "merge", "--abort"],
            capture_output=True,
            check=False,
        )
        raise


def _limpiar(rama: str) -> str | None:
    """Borra el worktree y la rama ya integrada. Devuelve el problema, si hubo."""
    actual, path = "", ""
    for linea in _git("worktree", "list", "--porcelain").splitlines():
        if linea.startswith("worktree "):
            actual = linea.removeprefix("worktree ")
        elif linea == f"branch refs/heads/{rama}":
            path = actual
    try:
        if path:
            _git("worktree", "remove", path)
        _git("branch", "-d", rama)
    except NoIntegrable as exc:
        return str(exc)
    return None


def _cerrar(con: Conexion, r: dict[str, Any], estado: str, agregado: str) -> None:
    con.execute(
        """UPDATE reportes_app SET estado = %s, nota = COALESCE(nota, '') || %s,
           actualizado_en = now() WHERE id = %s""",
        (estado, f"\n\n{agregado}", r["id"]),
    )
    print(
        f"{_ahora():%Y-%m-%d %H:%M} {r['rama']}: {estado} — {agregado}",
        flush=True,
    )


def _procesar(con: Conexion, r: dict[str, Any]) -> None:
    rama, hora = r["rama"] or "", f"{_ahora():%d/%m %H:%M}"
    try:
        if not _RAMA_VALIDA.match(rama):
            raise NoIntegrable(f"nombre de rama inválido: {rama!r}")
        archivos = [] if _ya_integrada(rama) else _verificar(rama)
        if archivos:
            _mergear(rama)
    except NoIntegrable as exc:
        motivo = f"No se pudo integrar ({hora}): {exc}"
        _cerrar(con, r, "resuelto", motivo)
        return
    reiniciar = any(a.startswith("backend/") for a in archivos)
    pasos = (
        "Tocó backend: falta reiniciar el backend."
        if reiniciar
        else "No hace falta reiniciar."
    )
    problema = _limpiar(rama)
    limpieza = f" No se pudo borrar el worktree/rama: {problema}" if problema else ""
    agregado = f"Integrada en develop ({hora}), sin pushear. {pasos}{limpieza}"
    _cerrar(con, r, "integrado", agregado)


def main() -> None:
    with conectar() as con:
        pendientes = con.execute(
            """SELECT id::text, rama FROM reportes_app
               WHERE estado = 'integrar' ORDER BY actualizado_en"""
        ).fetchall()
        for r in pendientes:
            _procesar(con, r)
            con.commit()


if __name__ == "__main__":
    main()

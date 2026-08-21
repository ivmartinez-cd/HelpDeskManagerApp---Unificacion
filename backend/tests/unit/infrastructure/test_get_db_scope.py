"""Guarda del ADR-030: toda inyección de `get_db` lleva `scope="function"`.

Con el scope por defecto de FastAPI (>= 0.118, "request") el commit de `get_db`
corre después de enviar la respuesta: el cliente recibe el 200 antes de que la
escritura exista (login → /me daba 401 bajo carga) y un error de commit no se
puede reportar. No hay forma de fijar el default a nivel app, así que se fija
por convención y este test la hace cumplir."""

import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3] / "src"
_SIN_SCOPE = re.compile(r"Depends\(\s*get_db\s*\)")


def test_todo_depends_get_db_lleva_scope_function() -> None:
    ofensores = [
        f"{path.relative_to(_SRC)}:{n}"
        for path in sorted(_SRC.rglob("*.py"))
        for n, linea in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _SIN_SCOPE.search(linea)
    ]
    assert ofensores == [], (
        "Depends(get_db) sin scope=\"function\" (ver ADR-030): " + ", ".join(ofensores)
    )

from types import SimpleNamespace
from typing import Any

from src.modules.contadores.infrastructure.siges.pyodbc_operador_gateway import _to_operador


def _row(**overrides: Any) -> SimpleNamespace:
    """Fila como la devuelve pyodbc (acceso por atributo, nombres de columna
    de la consulta)."""
    base: dict[str, Any] = {
        "login": "vipaez",
        "nombre": "Victor",
        "apellido": "Paez",
        "color": "#888200",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_mapea_una_fila_confirmada_contra_siges() -> None:
    """Mismo caso confirmado con dato real en ADR-012 (ronda 4)."""
    operador = _to_operador(_row())

    assert operador.id == "vipaez"
    assert operador.nombre == "Victor Paez"
    assert operador.color == "#888200"


def test_nombre_y_apellido_nulos_cae_al_login() -> None:
    operador = _to_operador(_row(nombre=None, apellido=None))

    assert operador.nombre == "vipaez"

"""Parsing de valores crudos de la tabla exportada — puerto de `csv_parser.py` del
legacy (`_parse_monto`/`_parse_fecha`), sin cambios de comportamiento: un monto
ilegible cae a 0.0, una fecha ilegible cae a `None`, nunca lanzan (el legacy tampoco
lo hacía — es texto exportado desde un sistema externo, no input validado)."""

from datetime import date, datetime
from typing import Any

_FORMATOS_FECHA = ("%Y%m%d", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y")
_VACIOS = ("", "-", "nan", "none")


def parse_monto(valor: Any) -> float:
    if valor is None:
        return 0.0
    texto = str(valor).strip().replace("$", "").replace(" ", "")
    if texto.lower() in _VACIOS:
        return 0.0
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def parse_fecha(valor: Any) -> date | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto.lower() in ("", "nan", "none"):
        return None
    for formato in _FORMATOS_FECHA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None

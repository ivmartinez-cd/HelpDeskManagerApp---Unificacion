"""Celdas de exports (CSV/Excel) a prueba de "formula injection": un texto que
empieza con = + - @ (ej. un nombre cargado por un usuario) Excel lo ejecuta como
fórmula al abrir el archivo. Se antepone un apóstrofo, que Excel muestra como
texto literal (auditoría de seguridad 2026-09-30). Los números no se tocan."""

import csv
from collections.abc import Iterable
from typing import Any

_INICIOS_PELIGROSOS = ("=", "+", "-", "@", "\t", "\r")


def celda_segura(valor: Any) -> Any:
    if isinstance(valor, str) and valor.startswith(_INICIOS_PELIGROSOS):
        return "'" + valor
    return valor


def fila_segura(valores: Iterable[Any]) -> list[Any]:
    return [celda_segura(v) for v in valores]


def desescapar_celda(valor: str) -> str:
    """Inversa para re-importar un CSV exportado por la app."""
    if valor.startswith("'") and valor[1:].startswith(_INICIOS_PELIGROSOS):
        return valor[1:]
    return valor


class CsvWriterSeguro:
    def __init__(self, destino: Any) -> None:
        self._writer = csv.writer(destino)

    def writerow(self, valores: Iterable[Any]) -> None:
        self._writer.writerow(fila_segura(valores))

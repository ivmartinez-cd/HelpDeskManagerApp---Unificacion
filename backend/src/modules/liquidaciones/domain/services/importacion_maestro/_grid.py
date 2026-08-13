"""Funciones que tratan una hoja de Excel como una matriz de celdas cruda
(`list[list[Any]]`, sin header fijo — estas hojas tienen celdas combinadas y una
fila de "AGENTE:" que flota antes del header real, así que no alcanza con
`pandas.read_excel(header=N)` como sí alcanzaba para el archivo de liquidaciones)."""

from collections.abc import Iterable, Sequence
from typing import Any

from src.modules.liquidaciones.domain.services.importacion_maestro._valores import (
    texto_o_none as _texto,
)


def _primera_celda_no_vacia(fila: Sequence[Any], desde: int) -> str | None:
    for celda in fila[desde:]:
        texto = _texto(celda)
        if texto:
            return texto
    return None


def buscar_valor_agente(grid: Sequence[Sequence[Any]]) -> str | None:
    """Busca una celda "AGENTE:" (match por prefijo, no exacto — soporta la forma
    inline "AGENTE: PENTACOM") y devuelve el nombre corto. Si la celda a la derecha
    está vacía (típico con celdas combinadas), sigue buscando la próxima celda no
    vacía en la misma fila — el legacy tomaba `idx+1` fijo y con una celda combinada
    ahí caía en `NaN`, terminaba creando un prestador literal `"nan"`."""
    for fila in grid:
        for idx, celda in enumerate(fila):
            etiqueta = _texto(celda)
            if not etiqueta:
                continue
            clave, _, inline = etiqueta.partition(":")
            if not clave.strip().upper().startswith("AGENTE"):
                continue
            valor = _texto(inline) or _primera_celda_no_vacia(fila, idx + 1)
            if valor:
                return valor
    return None


def detectar_fila_header(grid: Sequence[Sequence[Any]], marcador: str) -> int | None:
    """Índice de la primera fila que tenga una celda conteniendo `marcador`
    (case-insensitive, substring) — la fila de headers reales de estas hojas no
    está en una posición fija."""
    objetivo = marcador.strip().lower()
    for idx, fila in enumerate(grid):
        for celda in fila:
            texto = _texto(celda)
            if texto and objetivo in texto.lower():
                return idx
    return None


def _headers_unicos(fila_header: Sequence[Any]) -> dict[int, str]:
    vistos: set[str] = set()
    headers: dict[int, str] = {}
    for idx, celda in enumerate(fila_header):
        texto = _texto(celda)
        if not texto or texto in vistos:
            continue
        vistos.add(texto)
        headers[idx] = texto
    return headers


def grid_a_filas(grid: Sequence[Sequence[Any]], fila_header: int) -> list[dict[str, Any]]:
    """Arma dicts usando la fila `fila_header` como headers — columnas con header
    vacío se descartan, y ante headers repetidos gana la primera ocurrencia (pandas
    resolvía esto solo con `header=N`; acá se arma el dict a mano)."""
    headers = _headers_unicos(grid[fila_header])
    return [
        {nombre: (fila[idx] if idx < len(fila) else None) for idx, nombre in headers.items()}
        for fila in grid[fila_header + 1 :]
    ]


def buscar_columna(headers: Iterable[str], *alias: str) -> str | None:
    """Match EXACTO (case-insensitive) contra un header real — a propósito no es
    substring como `importacion/metadata.mapear_columnas` (ese vocabulario es de
    otro archivo; acá "tipo" haría match contra columnas como "Tipo de Equipo")."""
    objetivo = {a.strip().lower() for a in alias}
    for header in headers:
        if header.strip().lower() in objetivo:
            return header
    return None

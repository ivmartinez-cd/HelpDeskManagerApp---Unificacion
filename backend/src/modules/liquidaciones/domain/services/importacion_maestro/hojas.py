"""Detección de qué hoja del libro es la principal (tiene "AGENTE:") o la de Tabla
KM (nombre fuzzy), y extracción de la vigencia desde el nombre de archivo."""

import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from src.modules.liquidaciones.domain.services.importacion_maestro._grid import (
    buscar_valor_agente,
)

_PATRON_VIGENCIA = re.compile(r"(\d{6})\.\w+$")


def detectar_hoja_principal(hojas: Mapping[str, Sequence[Sequence[Any]]]) -> str | None:
    """Primera hoja (en el orden del libro) que tenga una celda "AGENTE:" — a
    diferencia del legacy (que buscaba una hoja literalmente llamada "ENERO"), no
    depende de cómo se llame la hoja ni de qué mes sea: un archivo de abril con
    hoja "ABRIL" rompía el legacy, acá no."""
    for nombre, grid in hojas.items():
        if buscar_valor_agente(grid) is not None:
            return nombre
    return None


def detectar_hoja_tabla_km(hojas: Mapping[str, Sequence[Sequence[Any]]]) -> str | None:
    """Fuzzy: nombre de hoja en minúsculas contiene "tabla" Y "km" (cubre "TABLA
    KMS", "TABLA DE KMS", "TABLA KMS 2023"...). Primer match gana, mismo criterio
    que el legacy. `None` si no hay ninguna — no es fatal, ver `constructor.py`."""
    for nombre in hojas:
        normalizado = nombre.lower()
        if "tabla" in normalizado and "km" in normalizado:
            return nombre
    return None


def parse_vigencia_desde_nombre(nombre_archivo: str, hoy: date) -> date:
    """Convención real del nombre de archivo: `<NOMBRE> <YYYYMM>.xlsx`. Sin match, o
    con mes fuera de 1-12, cae al primer día del mes de `hoy` — recibe `hoy` por
    parámetro (no llama `date.today()` acá) para ser testeable sin depender del
    reloj; el adapter es quien pasa `date.today()` en producción."""
    match = _PATRON_VIGENCIA.search(nombre_archivo)
    if match:
        anio, mes = int(match.group(1)[:4]), int(match.group(1)[4:])
        if 1 <= mes <= 12:
            return date(anio, mes, 1)
    return date(hoy.year, hoy.month, 1)

"""Metadata de la liquidación derivada del nombre de archivo y de las fechas de
cierre de sus incidentes — puerto de `_map_columns`/`_extract_numero_liquidacion`/
`_extract_tipo_liquidacion`/`_extract_periodo` del legacy `csv_parser.py`."""

import re
from collections.abc import Mapping, Sequence

from src.modules.liquidaciones.domain.entities.liquidacion import (
    TIPO_CC,
    TIPO_DEPOSITO,
    TIPO_PRECO,
    TIPO_REGULAR,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)

_PATRONES_COLUMNAS: Mapping[str, tuple[str, ...]] = {
    "numero_incidente": ("incidente", "nro incidente", "número incidente"),
    "rubro": ("rubro",),
    "tipo": ("tipo",),
    "empresa": ("empresa", "cliente"),
    "sucursal": ("sucursal",),
    "nro_serie": ("nro. serie", "nro serie", "serie", "número de serie"),
    "fecha_cierre": ("fecha cierre", "fecha de cierre", "cierre"),
    "costo_serv": ("costo serv", "costo servicio", "precio serv"),
    "cant_km": ("cant. km", "cant km", "cantidad km"),
    "costo_km": ("costo km", "precio km"),
    "total_viaje": ("total viaje", "viaje"),
    "costo_total": ("costo total", "total"),
    "pasa_it": ("p.it", "p. it", "pasa it", "pit"),
}


def mapear_columnas(columnas: Sequence[str]) -> dict[str, str]:
    """Para cada columna real de la tabla exportada, el primer patrón que matchea
    (en el orden fijo de arriba) gana — una columna sin patrón conocido queda fuera
    del mapeo (se ignora, igual que en el legacy)."""
    mapeo: dict[str, str] = {}
    for columna in columnas:
        columna_normalizada = str(columna).lower().strip()
        objetivo = _primer_patron_que_matchea(columna_normalizada)
        if objetivo is not None:
            mapeo[columna] = objetivo
    return mapeo


def _primer_patron_que_matchea(columna_normalizada: str) -> str | None:
    for objetivo, patrones in _PATRONES_COLUMNAS.items():
        if any(patron in columna_normalizada for patron in patrones):
            return objetivo
    return None


def extraer_numero_liquidacion(nombre_archivo: str) -> str:
    m = re.search(r"liquidacion[_-](\d+[-_]\d+)", nombre_archivo, re.IGNORECASE)
    return m.group(1).replace("_", "-") if m else ""


def extraer_tipo_liquidacion(nombre_archivo: str) -> str:
    nombre = nombre_archivo.lower()
    if "_preco" in nombre:
        return TIPO_PRECO
    if "_cc" in nombre or "centro_civico" in nombre or "centro civico" in nombre:
        return TIPO_CC
    if "deposito" in nombre or "bodega" in nombre:
        return TIPO_DEPOSITO
    return TIPO_REGULAR


def extraer_periodo(nombre_archivo: str, incidentes: Sequence[IncidenteImportado]) -> str:
    """1) el período más frecuente entre las fechas de cierre de los incidentes (más
    preciso); 2) si no hay ninguna, la fecha en el nombre del archivo asumiendo que
    se exportó el mes siguiente al liquidado; 3) `""` si ninguna de las dos sirve."""
    periodos = [
        f"{i.fecha_cierre.year}-{i.fecha_cierre.month:02d}" for i in incidentes if i.fecha_cierre
    ]
    if periodos:
        return max(set(periodos), key=periodos.count)
    return _periodo_desde_nombre_archivo(nombre_archivo)


def _periodo_desde_nombre_archivo(nombre_archivo: str) -> str:
    m = re.search(r"_(\d{4})(\d{2})\d{2}", nombre_archivo)
    if not m:
        return ""
    anio, mes = int(m.group(1)), int(m.group(2))
    if mes == 1:
        return f"{anio - 1}-12"
    return f"{anio}-{mes - 1:02d}"

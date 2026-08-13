"""Orquestador puro del Excel maestro: de `Mapping[nombre_hoja, grid]` (ya leído
del archivo por el adapter — sin pandas acá, solo listas/dicts) a
`ResultadoImportacionMaestro`."""

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from src.modules.liquidaciones.domain.errors import ArchivoMaestroInvalidoError
from src.modules.liquidaciones.domain.services.importacion_maestro._grid import (
    buscar_valor_agente,
    detectar_fila_header,
    grid_a_filas,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.hojas import (
    detectar_hoja_principal,
    detectar_hoja_tabla_km,
    parse_vigencia_desde_nombre,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.tabla_km import (
    extraer_spst_nombres,
    extraer_tabla_km,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.tarifarios import (
    extraer_tarifarios,
)
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    ResultadoImportacionMaestro,
    SpstImportado,
    TablaKmImportada,
    TarifarioImportado,
)

_MENSAJE_SIN_AGENTE = 'no se encontró el campo "AGENTE:" en ninguna hoja'


def armar_resultado_importacion_maestro(
    hojas: Mapping[str, Sequence[Sequence[Any]]], nombre_archivo: str, hoy: date
) -> ResultadoImportacionMaestro:
    nombre_hoja, nombre_corto = _resolver_hoja_principal(hojas)
    vigencia = parse_vigencia_desde_nombre(nombre_archivo, hoy)
    tarifarios = _extraer_tarifarios_de_hoja(hojas[nombre_hoja], vigencia)
    hoja_km, spsts, tabla_km = _extraer_tabla_km_y_spsts(hojas)
    return ResultadoImportacionMaestro(
        nombre_corto=nombre_corto,
        vigencia=vigencia,
        hoja_tabla_km=hoja_km,
        spsts=[SpstImportado(nombre=n) for n in spsts],
        tarifarios=tarifarios,
        tabla_km=tabla_km,
    )


def _resolver_hoja_principal(hojas: Mapping[str, Sequence[Sequence[Any]]]) -> tuple[str, str]:
    nombre_hoja = detectar_hoja_principal(hojas)
    if nombre_hoja is None:
        raise ArchivoMaestroInvalidoError(_MENSAJE_SIN_AGENTE)
    nombre_corto = buscar_valor_agente(hojas[nombre_hoja])
    if nombre_corto is None:
        raise ArchivoMaestroInvalidoError(_MENSAJE_SIN_AGENTE)
    return nombre_hoja, nombre_corto


def _extraer_tarifarios_de_hoja(
    grid: Sequence[Sequence[Any]], vigencia: date
) -> list[TarifarioImportado]:
    fila_header = detectar_fila_header(grid, "Incidente")
    if fila_header is None:
        return []
    return extraer_tarifarios(grid_a_filas(grid, fila_header), vigencia)


def _extraer_tabla_km_y_spsts(
    hojas: Mapping[str, Sequence[Sequence[Any]]],
) -> tuple[str | None, list[str], list[TablaKmImportada]]:
    nombre_hoja = detectar_hoja_tabla_km(hojas)
    if nombre_hoja is None:
        return None, [], []
    fila_header = detectar_fila_header(hojas[nombre_hoja], "Sucursal")
    if fila_header is None:
        return nombre_hoja, [], []
    filas = grid_a_filas(hojas[nombre_hoja], fila_header)
    return nombre_hoja, extraer_spst_nombres(filas), extraer_tabla_km(filas)

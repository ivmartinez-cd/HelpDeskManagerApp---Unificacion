"""Extracción de Tarifarios desde las filas de la hoja principal.

Reusa `normalizar_tipo_servicio` (mismo vocabulario que el importador de
liquidaciones — genuinamente el mismo texto libre "Tipo") pero agrega una
whitelist que esa función no tiene: texto que no matchea ningún tipo conocido (ej.
una celda "TOTAL GENERAL" de un pie de tabla) cae al texto crudo dentro de
`normalizar_tipo_servicio`; acá se descarta en vez de persistirse como tarifario
basura. Dedup **solo dentro del archivo** (por tipo+costo) — el dedup contra los
tarifarios ya existentes en la base (3 partes: tipo+costo+vigencia) es
responsabilidad del use case, que sí tiene acceso al repositorio."""

from collections.abc import Sequence
from datetime import date
from typing import Any

from src.modules.liquidaciones.domain.entities.tarifario import TIPOS_SERVICIO
from src.modules.liquidaciones.domain.services.importacion.normalizacion import (
    normalizar_tipo_servicio,
)
from src.modules.liquidaciones.domain.services.importacion_maestro._grid import buscar_columna
from src.modules.liquidaciones.domain.services.importacion_maestro._valores import (
    parse_numero_excel,
    texto_o_none,
)
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    TarifarioImportado,
)


def extraer_tarifarios(
    filas: Sequence[dict[str, Any]], vigencia: date
) -> list[TarifarioImportado]:
    if not filas:
        return []
    columnas = _resolver_columnas(list(filas[0].keys()))
    if columnas is None:
        return []
    vistos: set[tuple[str, float]] = set()
    resultado: list[TarifarioImportado] = []
    for fila in filas:
        tarifario = _construir_tarifario(fila, columnas, vigencia)
        if tarifario is None:
            continue
        clave = (tarifario.tipo_servicio, round(tarifario.costo_servicio, 2))
        if clave in vistos:
            continue
        vistos.add(clave)
        resultado.append(tarifario)
    return resultado


def _resolver_columnas(headers: Sequence[str]) -> tuple[str, str, str | None] | None:
    tipo = buscar_columna(headers, "Tipo")
    costo_serv = buscar_columna(headers, "Costo Serv", "Costo Servicio", "Precio Serv")
    if tipo is None or costo_serv is None:
        return None
    return tipo, costo_serv, buscar_columna(headers, "Costo Km", "Precio Km")


def _construir_tarifario(
    fila: dict[str, Any], columnas: tuple[str, str, str | None], vigencia: date
) -> TarifarioImportado | None:
    col_tipo, col_costo_serv, col_costo_km = columnas
    tipo_crudo = texto_o_none(fila.get(col_tipo))
    # `normalizar_tipo_servicio("")` cae a TIPO_CORRECTIVO por default (pensado para
    # el importador de liquidaciones, donde "sin tipo" == correctivo por regla de
    # negocio) — acá una celda de Tipo vacía es una fila basura, no un correctivo
    # implícito: el legacy la descartaba (`if not tipo: continue`), se replica.
    if tipo_crudo is None:
        return None
    tipo = normalizar_tipo_servicio(tipo_crudo)
    if tipo not in TIPOS_SERVICIO:
        return None
    costo_servicio = parse_numero_excel(fila.get(col_costo_serv))
    if costo_servicio is None or costo_servicio <= 0:
        return None
    costo_km = parse_numero_excel(fila.get(col_costo_km)) if col_costo_km else None
    return TarifarioImportado(
        tipo_servicio=tipo,
        costo_servicio=costo_servicio,
        costo_km=costo_km or 0.0,
        vigencia_desde=vigencia,
    )

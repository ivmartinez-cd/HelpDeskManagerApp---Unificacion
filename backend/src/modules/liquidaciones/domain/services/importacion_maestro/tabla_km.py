"""Extracción de nombres de SPST y filas de Tabla KM desde la hoja "Tabla KMS" (o
la variante fuzzy que haya detectado `hojas.detectar_hoja_tabla_km`).

`aplica_viatico`/`kms_a_facturar`/`umbral_viatico` NO se leen del Excel — se
recalculan siempre acá (regla de negocio, no del use case), mismo criterio que el
legacy: `RN005` documentada en `domain/entities/tabla_km.py` (excepción de umbral
para casos puntuales) se preserva porque una fila ya existente se omite en el use
case, nunca se pisa."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from src.modules.liquidaciones.domain.entities.tabla_km import UMBRAL_VIATICO_DEFAULT
from src.modules.liquidaciones.domain.services.importacion_maestro._grid import buscar_columna
from src.modules.liquidaciones.domain.services.importacion_maestro._valores import (
    parse_numero_excel,
    texto_o_none,
    url_o_none,
)
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    TablaKmImportada,
)


@dataclass(frozen=True)
class _ColumnasTablaKm:
    sucursal: str
    empresa: str
    kms: str
    prestador: str | None
    domicilio: str | None
    localidad: str | None
    provincia: str | None
    maps: str | None


def extraer_spst_nombres(filas: Sequence[dict[str, Any]]) -> list[str]:
    columnas = _resolver_columnas(list(filas[0].keys())) if filas else None
    if columnas is None or columnas.prestador is None:
        return []
    vistos: set[str] = set()
    nombres: list[str] = []
    for fila in filas:
        nombre = texto_o_none(fila.get(columnas.prestador))
        if nombre and nombre.lower() not in vistos:
            vistos.add(nombre.lower())
            nombres.append(nombre)
    return nombres


def extraer_tabla_km(filas: Sequence[dict[str, Any]]) -> list[TablaKmImportada]:
    if not filas:
        return []
    columnas = _resolver_columnas(list(filas[0].keys()))
    if columnas is None:
        return []
    construidas = (_construir_tabla_km(fila, columnas) for fila in filas)
    return [t for t in construidas if t is not None]


def _resolver_columnas(headers: Sequence[str]) -> _ColumnasTablaKm | None:
    sucursal = buscar_columna(headers, "Sucursal")
    empresa = buscar_columna(headers, "Empresa", "Cliente")
    kms = buscar_columna(headers, "Kms recorrido", "KM", "Kms")
    if sucursal is None or empresa is None or kms is None:
        return None
    return _ColumnasTablaKm(
        sucursal=sucursal,
        empresa=empresa,
        kms=kms,
        prestador=buscar_columna(headers, "Prestador", "Base"),
        domicilio=buscar_columna(headers, "Domicilio"),
        localidad=buscar_columna(headers, "Localidad"),
        provincia=buscar_columna(headers, "Provincia"),
        maps=buscar_columna(headers, "RECORRIDO", "Maps", "URL Maps"),
    )


def _texto_opcional(fila: dict[str, Any], columna: str | None) -> str | None:
    if columna is None:
        return None
    return texto_o_none(fila.get(columna))


def _construir_tabla_km(
    fila: dict[str, Any], columnas: _ColumnasTablaKm
) -> TablaKmImportada | None:
    empresa = texto_o_none(fila.get(columnas.empresa))
    sucursal = texto_o_none(fila.get(columnas.sucursal))
    kms_recorrido = parse_numero_excel(fila.get(columnas.kms))
    if not empresa or not sucursal or kms_recorrido is None:
        return None
    aplica_viatico = kms_recorrido > UMBRAL_VIATICO_DEFAULT
    return TablaKmImportada(
        empresa_nombre=empresa,
        sucursal_nombre=sucursal,
        domicilio_cliente=_texto_opcional(fila, columnas.domicilio),
        localidad_cliente=_texto_opcional(fila, columnas.localidad),
        provincia_cliente=_texto_opcional(fila, columnas.provincia),
        kms_recorrido=kms_recorrido,
        aplica_viatico=aplica_viatico,
        kms_a_facturar=kms_recorrido if aplica_viatico else 0.0,
        umbral_viatico=UMBRAL_VIATICO_DEFAULT,
        url_maps=url_o_none(fila.get(columnas.maps)) if columnas.maps else None,
        spst_nombre=_texto_opcional(fila, columnas.prestador),
    )

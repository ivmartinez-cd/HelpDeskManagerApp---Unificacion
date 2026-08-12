"""Orquestador puro de la importación: de filas ya mapeadas por `metadata.mapear_columnas`
(dict con las claves objetivo: numero_incidente/rubro/tipo/empresa/sucursal/nro_serie/
fecha_cierre/costo_serv/cant_km/costo_km/total_viaje/costo_total/pasa_it) a
`ResultadoImportacion`. Puerto de `parse_liquidacion` del legacy, sin la parte que lee
el archivo (esa vive en infrastructure — acá no hay pandas ni ningún I/O)."""

import re
from collections.abc import Mapping, Sequence
from typing import Any

from src.modules.liquidaciones.domain.services.importacion._valores import (
    parse_fecha,
    parse_monto,
)
from src.modules.liquidaciones.domain.services.importacion.metadata import (
    extraer_numero_liquidacion,
    extraer_periodo,
    extraer_tipo_liquidacion,
)
from src.modules.liquidaciones.domain.services.importacion.normalizacion import (
    normalizar_tipo_servicio,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
    ResultadoImportacion,
)

# "Incidente" (mayúscula inicial, sin acentos) aparece como fila cuando la tabla trae
# una fila de encabezado repetida en el cuerpo — mismo criterio exacto del legacy, sin
# normalizar mayúsculas (una fila real con "incidente" en minúsculas no debería darse).
_NUMERO_INCIDENTE_INVALIDO = ("nan", "Incidente")
_PATRON_NUMERO = re.compile(r"\d{5,7}[-–]\d+")


def construir_incidente_importado(fila: Mapping[str, Any]) -> IncidenteImportado | None:
    numero_crudo = str(fila.get("numero_incidente", "")).strip()
    if not numero_crudo or numero_crudo in _NUMERO_INCIDENTE_INVALIDO:
        return None

    match = _PATRON_NUMERO.search(numero_crudo)
    numero = match.group() if match else numero_crudo
    tipo_crudo = str(fila.get("tipo", "correctivo")).strip()

    return IncidenteImportado(
        numero_incidente=numero,
        rubro=str(fila.get("rubro", "")).strip() or "Impresoras",
        tipo=normalizar_tipo_servicio(tipo_crudo),
        empresa_nombre=str(fila.get("empresa", "")).strip(),
        sucursal_nombre=str(fila.get("sucursal", "")).strip(),
        nro_serie=str(fila.get("nro_serie", "")).strip(),
        fecha_cierre=parse_fecha(fila.get("fecha_cierre")),
        costo_servicio_cobrado=parse_monto(fila.get("costo_serv", 0)),
        cant_km_cobrado=parse_monto(fila.get("cant_km", 0)),
        costo_km_cobrado=parse_monto(fila.get("costo_km", 0)),
        total_viaje_cobrado=parse_monto(fila.get("total_viaje", 0)),
        costo_total_cobrado=parse_monto(fila.get("costo_total", 0)),
        pasa_it=str(fila.get("pasa_it", "SI")).strip().upper() != "NO",
    )


def armar_resultado_importacion(
    nombre_archivo: str, filas: Sequence[Mapping[str, Any]]
) -> ResultadoImportacion:
    posibles = (construir_incidente_importado(fila) for fila in filas)
    incidentes = [i for i in posibles if i is not None]
    return ResultadoImportacion(
        numero_liquidacion=extraer_numero_liquidacion(nombre_archivo),
        periodo=extraer_periodo(nombre_archivo, incidentes),
        tipo_liquidacion=extraer_tipo_liquidacion(nombre_archivo),
        incidentes=incidentes,
    )

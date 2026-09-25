"""Aplicación de tipificaciones guardadas a los incidentes (fase "solo caché"
del legacy: el reporte se arma sin llamar a la IA y cuenta los pendientes)."""

import hashlib
from dataclasses import dataclass, replace

from src.modules.reporte_incidentes.domain.entities.categoria import TipificacionGuardada
from src.modules.reporte_incidentes.domain.entities.incidente import Incidente

PENDIENTE = "Pendiente de revision"
SIN_CLASIFICAR = "Sin Clasificar"
SIN_SUBCATEGORIA = "Sin subcategorizar"
CONFIANZA_ALTA = "alta"
# Color fijo con que el legacy pinta "Pendiente de revision" (no es una categoría).
COLOR_PENDIENTE = "#9aa0a6"
COLOR_SIN_CLASIFICAR = "#6b7689"


def clave_de(descripcion: str, causa: str | None, solucion: str | None) -> str:
    """Clave de la caché: el mismo texto que ve la IA (+ causa), así dos
    incidentes con idéntico contenido comparten tipificación."""
    return f"{descripcion}|{causa or ''}|{solucion or ''}"


def clave_caso(incidente: Incidente) -> str:
    return clave_de(incidente.descripcion, incidente.causa, incidente.solucion)


def hash_clave(clave: str) -> str:
    """La clave puede ser larga (bitácoras enteras): se indexa por su sha256."""
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def aplicar_umbral(guardada: TipificacionGuardada) -> tuple[str, str]:
    """Solo la confianza "alta" se muestra; media/baja quedan pendientes de revisión."""
    if guardada.confianza.lower() == CONFIANZA_ALTA:
        return guardada.categoria, guardada.subcategoria
    return PENDIENTE, ""


@dataclass(frozen=True, slots=True)
class ResultadoTipificacion:
    incidentes: list[Incidente]
    # Casos distintos sin tipificación guardada (los que la IA todavía debe ver).
    pendientes: int


def tipificar_desde_cache(
    incidentes: list[Incidente], cache: dict[str, TipificacionGuardada]
) -> ResultadoTipificacion:
    """`cache` va indexada por `clave_caso`. Los incidentes sin descripción no
    se tipifican ni cuentan como pendientes (igual que el legacy)."""
    sin_cache = {
        clave_caso(i) for i in incidentes if i.descripcion and clave_caso(i) not in cache
    }
    tipificados = [
        _con_tipificacion(i, cache.get(clave_caso(i)) if i.descripcion else None)
        for i in incidentes
    ]
    return ResultadoTipificacion(tipificados, len(sin_cache))


def _con_tipificacion(incidente: Incidente, guardada: TipificacionGuardada | None) -> Incidente:
    if guardada is None:
        return replace(incidente, categoria=PENDIENTE, subcategoria="")
    categoria, subcategoria = aplicar_umbral(guardada)
    return replace(incidente, categoria=categoria, subcategoria=subcategoria)

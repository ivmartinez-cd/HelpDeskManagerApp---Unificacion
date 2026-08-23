"""Mapeo de filas pyodbc a entidades — acceso por nombre de columna (falla
ruidoso con AttributeError si la consulta cambia), mismo criterio que
sla/infrastructure/mercurio/row_mapping.py."""

from typing import Any

from src.modules.preventivos.domain.entities.equipo_preventivo import EquipoPreventivo
from src.modules.preventivos.domain.entities.sucursal_coordenadas import (
    SucursalParaGeocoding,
)
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque


def _parse_coordenada(valor: Any) -> float | None:
    """`Sucursal.Latitud`/`Longitud` son texto libre en Siges: puede venir con
    coma decimal, vacío o directamente basura no numérica. Nunca levanta —
    la validación de rango es responsabilidad de domain/services/coordenadas.py."""
    if valor is None:
        return None
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def map_equipo_row(row: Any) -> EquipoPreventivo:
    fecha = row.fecha_ultimo_preventivo
    return EquipoPreventivo(
        id_maquina=int(row.id_maquina),
        id_sucursal=int(row.id_sucursal),
        serie=(row.serie or "").strip(),
        modelo=(row.modelo or "").strip(),
        cliente=(row.cliente or "").strip(),
        sucursal=(row.sucursal or "").strip(),
        zona=(row.zona or "").strip(),
        frecuencia_dias=int(row.frecuencia_dias) if row.frecuencia_dias is not None else None,
        fecha_ultimo_preventivo=fecha.date() if fecha is not None else None,
        latitud=_parse_coordenada(row.latitud),
        longitud=_parse_coordenada(row.longitud),
    )


def map_zona_row(row: Any) -> ZonaParque:
    return ZonaParque(zona=(row.zona or "").strip(), maquinas_activas=int(row.maquinas_activas))


def map_sucursal_geocoding_row(row: Any) -> SucursalParaGeocoding:
    return SucursalParaGeocoding(
        id_sucursal=int(row.id_sucursal),
        cliente=(row.cliente or "").strip(),
        sucursal=(row.sucursal or "").strip(),
        domicilio=(row.domicilio or "").strip(),
        ciudad=(row.ciudad or "").strip(),
        provincia=(row.provincia or "").strip(),
        latitud=_parse_coordenada(row.latitud),
        longitud=_parse_coordenada(row.longitud),
    )

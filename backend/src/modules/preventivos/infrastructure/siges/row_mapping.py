"""Mapeo de filas pyodbc a entidades — acceso por nombre de columna (falla
ruidoso con AttributeError si la consulta cambia), mismo criterio que
sla/infrastructure/mercurio/row_mapping.py."""

from typing import Any

from src.modules.preventivos.domain.entities.equipo_preventivo import EquipoPreventivo
from src.modules.preventivos.domain.entities.zona_parque import ZonaParque


def map_equipo_row(row: Any) -> EquipoPreventivo:
    fecha = row.fecha_ultimo_preventivo
    return EquipoPreventivo(
        id_maquina=int(row.id_maquina),
        serie=(row.serie or "").strip(),
        modelo=(row.modelo or "").strip(),
        cliente=(row.cliente or "").strip(),
        sucursal=(row.sucursal or "").strip(),
        zona=(row.zona or "").strip(),
        frecuencia_dias=int(row.frecuencia_dias) if row.frecuencia_dias is not None else None,
        fecha_ultimo_preventivo=fecha.date() if fecha is not None else None,
    )


def map_zona_row(row: Any) -> ZonaParque:
    return ZonaParque(zona=(row.zona or "").strip(), maquinas_activas=int(row.maquinas_activas))

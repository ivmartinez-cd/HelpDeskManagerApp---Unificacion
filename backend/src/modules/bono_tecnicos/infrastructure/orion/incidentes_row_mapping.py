"""Mapeo de una fila pyodbc de `incidentes_query.py` a la entidad de dominio.

Acceso por nombre de columna (pyodbc.Row lo expone como atributo), no por
índice posicional — mismo criterio que `row_mapping.py`."""

from typing import Any

from src.modules.bono_tecnicos.domain.entities.incidente_bono import IncidenteBono


def _texto(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def map_row(row: Any) -> IncidenteBono:
    return IncidenteBono(
        id_incidente=int(row.IdIncidente),
        categoria=_texto(row.Categoria),
        cliente=_texto(row.Cliente),
        sucursal=_texto(row.Sucursal),
        nro_serie=_texto(row.NroSerie),
    )

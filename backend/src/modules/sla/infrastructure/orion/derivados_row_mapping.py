"""Mapeo de filas pyodbc de la query de Incidentes Derivados a la entidad de
dominio. Acceso por nombre de columna, no por índice posicional."""

from typing import Any

from src.modules.sla.domain.entities.incidente_derivado import IncidenteDerivado


def _texto(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _entero(value: Any) -> int:
    return int(value) if value is not None else 0


def map_row(row: Any) -> IncidenteDerivado:
    return IncidenteDerivado(
        id_incidente=int(row.ID_Incidente),
        fecha_ingreso=row.Fecha_Ingreso,
        tipo=_texto(row.Tipo),
        estado=_texto(row.Estado),
        cliente=_texto(row.Den_Comercial),
        sucursal=_texto(row.Sucursal),
        nro_serie=_texto(row.Nro_Serie),
        modelo=_texto(row.Modelo),
        tecnico=_texto(row.Tecnico),
        id_tecnico=_entero(row.IdTecnico),
        dias_desde_ingreso=_entero(row.DiasDesdeIngreso),
    )

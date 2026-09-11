"""Mapeo de una fila pyodbc de la consulta de Siges a la entidad de dominio.

Acceso por nombre de columna (pyodbc.Row lo expone como atributo), no por
índice posicional: si la consulta cambia de orden, esto falla ruidoso con
AttributeError en vez de mapear silenciosamente un campo en otro."""

from typing import Any

from src.modules.sla.domain.entities.incidente_sla import IncidenteSla


def _texto(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _entero(value: Any) -> int:
    # HorasVencido llega como VARCHAR desde el CASE de la consulta; SLA puede
    # venir NULL en incidentes viejos sin SLA cargado.
    return int(value) if value is not None else 0


def map_row(row: Any) -> IncidenteSla:
    return IncidenteSla(
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
        region=_texto(row.REGION),
        fecha_operativo=row.FechaOperativo,
        periodo=_entero(row.Periodo),
        tiempo=_texto(row.Tiempo),
        rango=_texto(row.RANGO),
        sla_horas=_entero(row.SLA),
        horas_vencido=_entero(row.HorasVencido),
        resultado=_texto(row.Resultado),
    )

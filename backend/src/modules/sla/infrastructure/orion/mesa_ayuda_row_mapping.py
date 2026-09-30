"""Mapeo de filas pyodbc de la query de Mesa de Ayuda a la entidad de dominio.
Acceso por nombre de columna, no por índice posicional."""

from typing import Any

from src.modules.sla.domain.entities.incidente_mesa_ayuda import IncidenteMesaAyuda


def _texto(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _entero(value: Any) -> int:
    return int(value) if value is not None else 0


def _entero_o_none(value: Any) -> int | None:
    return int(value) if value is not None else None


def _operador(row: Any, login: str) -> str:
    nombre = f"{_texto(row.OperadorNombre)} {_texto(row.OperadorApellido)}".strip()
    return nombre or login


def map_row(row: Any) -> IncidenteMesaAyuda:
    login = _texto(row.OperadorLogin)
    return IncidenteMesaAyuda(
        id_incidente=int(row.ID_Incidente),
        fecha_ingreso=row.Fecha_Ingreso,
        tipo=_texto(row.Tipo),
        estado=_texto(row.Estado),
        cliente=_texto(row.Den_Comercial),
        sucursal=_texto(row.Sucursal),
        nro_serie=_texto(row.Nro_Serie),
        modelo=_texto(row.Modelo),
        operador_login=login,
        operador=_operador(row, login),
        dias_transcurridos=_entero(row.DiasTranscurridos),
        visita_id_incidente=_entero_o_none(row.VisitaId),
        visita_tecnico=_texto(row.VisitaTecnico) or None,
        visita_estado=_texto(row.VisitaEstado) or None,
        visitas_en_sucursal=_entero(row.VisitaCantidad),
    )

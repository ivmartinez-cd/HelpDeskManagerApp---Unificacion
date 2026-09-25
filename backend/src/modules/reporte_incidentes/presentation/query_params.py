"""Parámetros de query compartidos por los routers del módulo."""

from fastapi import Query

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import PedidoReporte
from src.modules.reporte_incidentes.domain.services.filtros import Filtros


def pedido_reporte(
    empresa_id: str = Query(..., min_length=1),
    periodo: str | None = Query(None, description="Mes final AAAA-MM (default: el actual)"),
    meses: int | None = Query(None, description="Cantidad de meses del rango (1 a 24)"),
) -> PedidoReporte:
    return PedidoReporte(empresa_id=empresa_id, periodo=periodo, meses=meses)


def filtros_crudos(sucursal: str = "", categoria: str = "", subcategoria: str = "") -> Filtros:
    return Filtros(sucursal=sucursal, categoria=categoria, subcategoria=subcategoria)

"""Lógica pura de `SincronizarCotizacionesDolar`: de la serie histórica
completa de ArgentinaDatos, para cada período (YYYY-MM) dentro del rango
pedido, el último registro con datos (cierre de mes)."""

from src.modules.liquidaciones.domain.repositories.cotizaciones_dolar_externas import (
    CotizacionDiaria,
)


def planificar_cierres_de_mes(
    serie: list[CotizacionDiaria], desde_periodo: str, hasta_periodo_excluyendo: str
) -> dict[str, CotizacionDiaria]:
    por_periodo: dict[str, CotizacionDiaria] = {}
    for dia in serie:
        periodo = f"{dia.fecha.year:04d}-{dia.fecha.month:02d}"
        if periodo < desde_periodo or periodo >= hasta_periodo_excluyendo:
            continue
        actual = por_periodo.get(periodo)
        if actual is None or dia.fecha > actual.fecha:
            por_periodo[periodo] = dia
    return por_periodo

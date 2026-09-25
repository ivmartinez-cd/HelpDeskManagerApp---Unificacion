"""Cuántos incidentes pedirle a wsAyC y cuáles quedarse.

`getTopIncidents` NO filtra por fecha: devuelve las N filas más recientes y el
mes se filtra acá. Por eso el `Top` depende de qué tan ATRÁS está el mes más
viejo pedido, no de cuántos meses abarca el rango (dimensionarlo por la
longitud hacía que "1 mes / Julio 2025" devolviera 0 incidentes). Es el mismo
valor para todos los meses de un rango, así comparten una única descarga."""

from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.services.bitacora import ESTADOS_CERRADOS
from src.modules.reporte_incidentes.domain.value_objects.periodo import Periodo, meses_entre


def top_para(mas_viejo: Periodo, actual: Periodo, limite_por_mes: int) -> int:
    return max(1, meses_entre(mas_viejo, actual)) * limite_por_mes


def cerrados_del_periodo(incidentes: list[Incidente], periodo: Periodo) -> list[Incidente]:
    """Solo los Resuelto/Cerrado cuya fecha cae en el mes (se enriquecen después)."""
    prefijo = str(periodo)
    return [
        i for i in incidentes
        if i.fecha.startswith(prefijo) and (i.estado or "") in ESTADOS_CERRADOS
    ]

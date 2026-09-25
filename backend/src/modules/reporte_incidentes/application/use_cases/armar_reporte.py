"""Arma el reporte de un cliente para un rango de meses (fase "solo caché").

Port de `buildRangeReport`/`buildReport`/`listIncidents`: baja una vez los
incidentes recientes, se queda con los cerrados de cada mes, los enriquece con
bitácora y detalle, y les aplica las tipificaciones guardadas sin llamar a la
IA. Los que no tienen tipificación quedan "Pendiente de revision" y se cuentan
para que la pantalla dispare la tipificación con IA aparte."""

import asyncio
from dataclasses import dataclass, replace
from datetime import date, datetime

from src.modules.reporte_incidentes.domain.entities.categoria import Categoria
from src.modules.reporte_incidentes.domain.entities.incidente import Empresa, Incidente
from src.modules.reporte_incidentes.domain.errors import (
    EmpresaNoEncontradaError,
    PeriodoInvalidoError,
)
from src.modules.reporte_incidentes.domain.repositories.incidentes_gateway import (
    IncidentesGateway,
)
from src.modules.reporte_incidentes.domain.repositories.tipificacion_repositories import (
    TaxonomiaRepository,
    TipificacionCacheRepository,
)
from src.modules.reporte_incidentes.domain.services import bitacora, ventana
from src.modules.reporte_incidentes.domain.services.tipificacion import (
    clave_caso,
    tipificar_desde_cache,
)
from src.modules.reporte_incidentes.domain.value_objects.periodo import (
    MAX_MESES_RANGO,
    Periodo,
    acotar_meses,
    periodos_recientes,
    rango_periodos,
)


@dataclass(frozen=True, slots=True)
class PedidoReporte:
    empresa_id: str
    periodo: str | None
    meses: int | None


@dataclass(frozen=True, slots=True)
class ReporteArmado:
    empresa: Empresa
    hasta: Periodo
    meses: int
    periodos: list[Periodo]
    incidentes: list[Incidente]
    pendientes: int
    taxonomia: list[Categoria]
    generado_en: datetime


def elegir_periodo(raw: str | None, hoy: date) -> Periodo:
    """Como el legacy: fuera de los últimos 24 meses (o inválido) => el mes actual."""
    recientes = periodos_recientes(MAX_MESES_RANGO, hoy)
    try:
        pedido = Periodo.parse(raw or "")
    except PeriodoInvalidoError:
        return recientes[0]
    return pedido if pedido in recientes else recientes[0]


class ArmarReporte:
    def __init__(
        self,
        gateway: IncidentesGateway,
        repos: tuple[TaxonomiaRepository, TipificacionCacheRepository],
        limite_por_mes: int,
    ) -> None:
        self._gateway = gateway
        self._taxonomia, self._cache = repos
        self._limite_por_mes = limite_por_mes

    async def execute(self, pedido: PedidoReporte) -> ReporteArmado:
        hoy = date.today()
        hasta, meses = elegir_periodo(pedido.periodo, hoy), acotar_meses(pedido.meses)
        empresa = await self._empresa(pedido.empresa_id)
        periodos = rango_periodos(hasta, meses)
        top = ventana.top_para(periodos[0], Periodo.de_fecha(hoy), self._limite_por_mes)
        recientes = await self._gateway.incidentes_recientes(empresa, top)
        por_mes = list(await asyncio.gather(*(self._mes(recientes, p) for p in periodos)))
        tipificados, pendientes = await self._tipificar(por_mes)
        return ReporteArmado(
            empresa, hasta, meses, periodos, tipificados, pendientes,
            await self._taxonomia.listar(), datetime.now().astimezone(),
        )

    async def _empresa(self, empresa_id: str) -> Empresa:
        empresas = await self._gateway.listar_empresas()
        empresa = next((e for e in empresas if e.id == empresa_id), None)
        if empresa is None:
            raise EmpresaNoEncontradaError(empresa_id)
        return empresa

    async def _mes(self, recientes: list[Incidente], periodo: Periodo) -> list[Incidente]:
        cerrados = ventana.cerrados_del_periodo(recientes, periodo)
        return list(await asyncio.gather(*(self._enriquecer(i) for i in cerrados)))

    async def _enriquecer(self, incidente: Incidente) -> Incidente:
        trabajos, detalle = await asyncio.gather(
            self._gateway.trabajos(incidente.id), self._gateway.detalle(incidente.id)
        )
        observacion = bitacora.observacion_de_apertura(trabajos)
        return replace(
            incidente,
            trabajos=tuple(trabajos),
            solucion=bitacora.derivar_solucion(trabajos),
            descripcion=bitacora.descripcion_completa(incidente.descripcion, observacion),
            causa=detalle.causa,
            tecnico=detalle.tecnico,
            tipo_trabajo=incidente.tipo_trabajo or detalle.tipo_trabajo,
            fecha_cierre=incidente.fecha_cierre or detalle.fecha_cierre,
        )

    async def _tipificar(self, por_mes: list[list[Incidente]]) -> tuple[list[Incidente], int]:
        """Pendientes = suma de casos sin tipificar de cada mes (como el legacy)."""
        claves = {clave_caso(i) for mes in por_mes for i in mes}
        cache = await self._cache.obtener(claves)
        resultados = [tipificar_desde_cache(mes, cache) for mes in por_mes]
        incidentes = [i for r in resultados for i in r.incidentes]
        return incidentes, sum(r.pendientes for r in resultados)

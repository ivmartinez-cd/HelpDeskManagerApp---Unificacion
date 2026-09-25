"""Tipifica con IA los casos del reporte que no tienen tipificación guardada
(port de `refineClassificationAction` + `classifyIncidents({useAi: true})`).

Solo van a la IA los casos SIN nada en caché: los guardados con confianza
media/baja se muestran pendientes pero no se re-tipifican (igual que el legacy;
los resuelve la revisión manual). Casos deduplicados por contenido, en lotes,
con pedidos en paralelo acotados. Se guarda la respuesta cruda (con su
confianza) solo si la IA respondió y la categoría existe en la taxonomía."""

import asyncio
import logging
from dataclasses import asdict, dataclass

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import (
    ArmarReporte,
    PedidoReporte,
)
from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)
from src.modules.reporte_incidentes.domain.entities.incidente import Incidente
from src.modules.reporte_incidentes.domain.errors import IaNoConfiguradaError
from src.modules.reporte_incidentes.domain.repositories.clasificador_ia import ClasificadorIA
from src.modules.reporte_incidentes.domain.repositories.tipificacion_repositories import (
    TipificacionCacheRepository,
)
from src.modules.reporte_incidentes.domain.services import prompt_tipificacion as prompt
from src.modules.reporte_incidentes.domain.services.tipificacion import PENDIENTE, clave_caso
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConfigIA:
    lote: int
    concurrencia: int
    precio_entrada_por_millon: float
    precio_salida_por_millon: float


@dataclass(frozen=True, slots=True)
class ResultadoIA:
    casos: int
    tipificados: int
    fallidos: int  # casos de lotes en los que la IA no respondió
    llamadas: int
    tokens_entrada: int
    tokens_salida: int
    costo_usd: float


@dataclass(frozen=True, slots=True)
class _Lote:
    tipificaciones: dict[str, TipificacionGuardada]
    llamadas: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    fallidos: int = 0


class TipificarPendientes:
    def __init__(
        self,
        armar: ArmarReporte,
        dependencias: tuple[TipificacionCacheRepository, ClasificadorIA],
        config: ConfigIA,
    ) -> None:
        self._armar = armar
        self._cache, self._ia = dependencias
        self._config = config

    async def execute(self, pedido: PedidoReporte) -> ResultadoIA:
        if not self._ia.configurado:
            raise IaNoConfiguradaError()
        reporte = await self._armar.execute(pedido)
        casos = await self._sin_cache(reporte.incidentes)
        semaforo = asyncio.Semaphore(self._config.concurrencia)
        tam = self._config.lote
        lotes = [casos[i : i + tam] for i in range(0, len(casos), tam)]
        resultados = await asyncio.gather(
            *(self._lote(lote, reporte.taxonomia, semaforo) for lote in lotes)
        )
        await self._cache.guardar({k: v for r in resultados for k, v in r.tipificaciones.items()})
        return self._resumen(len(casos), resultados)

    async def _sin_cache(self, incidentes: list[Incidente]) -> list[Incidente]:
        candidatos = {
            clave_caso(i): i for i in incidentes if i.categoria == PENDIENTE and i.descripcion
        }
        guardadas = await self._cache.obtener(set(candidatos))
        return [i for clave, i in candidatos.items() if clave not in guardadas]

    async def _lote(
        self, casos: list[Incidente], taxonomia: list[Categoria], semaforo: asyncio.Semaphore
    ) -> _Lote:
        texto = prompt.armar_prompt(
            taxonomia,
            [prompt.renderizar_caso(n, c.descripcion, c.solucion) for n, c in enumerate(casos)],
        )
        async with semaforo:
            try:
                respuesta = await self._ia.clasificar(texto)
            except ExternalServiceError:
                # Ya logueado en el adapter: el lote queda pendiente, sin inventar nada.
                return _Lote({}, fallidos=len(casos))
        predicciones = prompt.interpretar_respuesta(respuesta.texto, len(casos), taxonomia)
        guardables = {
            clave_caso(c): p for c, p in zip(casos, predicciones, strict=True)
            if p.categoria != PENDIENTE
        }
        return _Lote(guardables, 1, respuesta.tokens_entrada, respuesta.tokens_salida)

    def _resumen(self, casos: int, lotes: list[_Lote]) -> ResultadoIA:
        entrada = sum(r.tokens_entrada for r in lotes)
        salida = sum(r.tokens_salida for r in lotes)
        costo = (
            entrada * self._config.precio_entrada_por_millon
            + salida * self._config.precio_salida_por_millon
        ) / 1_000_000
        resultado = ResultadoIA(
            casos=casos,
            tipificados=sum(len(r.tipificaciones) for r in lotes),
            fallidos=sum(r.fallidos for r in lotes),
            llamadas=sum(r.llamadas for r in lotes),
            tokens_entrada=entrada,
            tokens_salida=salida,
            costo_usd=round(costo, 6),
        )
        logger.info(
            "reporte_incidentes: tipificación con IA", extra={"ia_costo": asdict(resultado)}
        )
        return resultado

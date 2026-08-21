"""Filtra el backlog de clientes pendientes (arrastre de calendario, ver
`GetPendingClientsUseCase`) contra el estado real de cierre en Siges: un
cliente sale del backlog si su grupo económico cruza contra Siges y NINGUNO
de sus anexos de Impresión activos sigue con un período anterior al mes en
curso sin facturar (ya lo facturaron, ya está A LIBERAR o ya rodó al mes en
curso — misma definición de "pendiente" que el reporte de anexos).

Si el cliente no tiene ningún anexo de Impresión activo en Siges, o el cruce
de nombre no encuentra candidato, se conserva sin cambios: no hay señal para
decidir, y ocultar un pendiente real sería peor que dejar un falso positivo
(mismo criterio de resiliencia que `MapaOperadorPorEmpresa`: "sin cruce, no
se inventa"). Si Siges no responde, tampoco se filtra nada."""

import logging

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.domain.ports.estado_cierre_grupos_port import EstadoCierreGruposPort
from src.modules.contadores.domain.services.cliente_matcher import (
    ALIAS_CLIENTE_GRUPO_NORM,
    IndiceNombres,
    buscar_por_nombre,
    normalizar_nombre,
)
from src.shared.domain.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class FiltrarPendientesPorPeriodoReal:
    def __init__(self, port: EstadoCierreGruposPort) -> None:
        self._port = port

    async def execute(
        self, pendientes: list[CalendarEventAnotado]
    ) -> list[CalendarEventAnotado]:
        if not pendientes:
            return pendientes
        try:
            snapshot = await self._port.list_estado()
        except ExternalServiceError as exc:
            logger.warning(
                "Sin cruce contra el período real de Siges; el backlog de "
                "pendientes de la card de Inicio degrada a mostrarse sin filtrar",
                extra={"cantidad_pendientes": len(pendientes)},
                exc_info=exc,
            )
            return pendientes
        indice = IndiceNombres(
            {normalizar_nombre(g.grupo): g.sin_cerrar for g in snapshot.grupos}
        )
        return [p for p in pendientes if self._sin_cerrar(p.event.cliente, indice) is not False]

    @staticmethod
    def _sin_cerrar(cliente: str | None, indice: IndiceNombres[bool]) -> bool | None:
        directo = buscar_por_nombre(cliente, indice)
        if directo is not None or not cliente:
            return directo
        grupo_alias = ALIAS_CLIENTE_GRUPO_NORM.get(normalizar_nombre(cliente))
        return None if grupo_alias is None else indice.exacto.get(grupo_alias)

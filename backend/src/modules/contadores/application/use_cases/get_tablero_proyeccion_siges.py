"""Tablero de Proyección con datos reales de Siges — mismo pipeline que el
modo ejemplo (`get_tablero_proyeccion.py`), reemplazando la fuente de
equipos por la consulta real (MODELO_DE_DATOS.md §3.4) y restaurando las
decisiones que el operador ya tomó en ESTE proceso."""

from collections.abc import Callable
from datetime import datetime

from src.modules.contadores.application.dtos.decision_operador_dto import (
    SolicitudRestauracionDto,
)
from src.modules.contadores.application.dtos.equipo_proceso_dto import EquipoProceso
from src.modules.contadores.application.dtos.resumen_proyeccion_dto import ResumenProyeccionDto
from src.modules.contadores.application.dtos.solicitud_tablero_siges_dto import (
    SolicitudTableroSigesDto,
)
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    contexto_proceso_siges,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.application.use_cases.get_tablero_proyeccion import (
    GetTableroProyeccionUseCase,
    TableroProyeccionResult,
    releer_lecturas_de_siges,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import CandidatosEquipoPort
from src.modules.contadores.domain.ports.decisiones_operador_port import DecisionesOperadorPort
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort

_RESUMEN_VACIO = ResumenProyeccionDto(reales=0, estimados=0, pendientes=0, sospechosos=0, total=0)
_ObtenerEquipos = Callable[[], list[EquipoProceso]]


class GetTableroProyeccionSigesUseCase:
    """`candidatos` (opcional) relee de Siges, por `ID_Contador`, la
    Partida/Llegada de una P/L manual guardada — como
    `ReconstruirOverrideAsync` del legacy; sin él se usan las lecturas que
    quedaron guardadas con la decisión."""

    def __init__(
        self,
        gateway: GrillaEstimacionPort,
        decisiones: DecisionesOperadorPort,
        recesos_store: RecesosPort,
        candidatos: CandidatosEquipoPort | None = None,
    ) -> None:
        self._gateway = gateway
        self._decisiones = decisiones
        self._recesos_store = recesos_store
        self._candidatos = candidatos

    async def execute(
        self, solicitud: SolicitudTableroSigesDto, descartar_hasta: datetime | None = None
    ) -> TableroProyeccionResult:
        # Cada carga del tablero consulta Siges de nuevo (legacy
        # `Index.CargarTablero`): lo que cargó otro operador hace un rato no
        # sirve si ya se registraron lecturas reales nuevas.
        filas_siges = await self._gateway.fetch_grilla(
            solicitud.nro_proceso,
            solicitud.fecha_objetivo,
            fresca=True,
            operador=solicitud.operador,
        )
        if not filas_siges:
            return TableroProyeccionResult([], _RESUMEN_VACIO)
        equipos = agrupar_por_equipo(filas_siges)
        ctx = await contexto_proceso_siges(
            filas_siges[0], solicitud.fecha_objetivo, solicitud.id_anexo, self._recesos_store
        )
        restauracion = SolicitudRestauracionDto(solicitud.nro_proceso, descartar_hasta)
        return await self._tablero(lambda: equipos).execute(ctx, restauracion)

    def _tablero(self, obtener_equipos: _ObtenerEquipos) -> GetTableroProyeccionUseCase:
        releer = (
            releer_lecturas_de_siges(self._candidatos) if self._candidatos is not None else None
        )
        return GetTableroProyeccionUseCase(self._decisiones, obtener_equipos, releer)

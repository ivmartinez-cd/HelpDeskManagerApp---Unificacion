"""Compartido por el panel de candidatos y las acciones del operador
(`proyeccion_operador/solicitud_real.entrada_de`, que alimenta
`recalcular_pl` / `forzar_metodo`): resuelven el mismo `EstimacionInput`
real (filtrar la última grilla cargada por equipo/clase, agrupar, armar
contexto y recesos) antes de aplicar su override manual puntual.
`contexto_proceso_siges` arma el contexto igual que el tablero, para que
ambos caminos vean los mismos recesos."""

from datetime import date

from src.modules.contadores.application.dtos.contexto_proceso_dto import ContextoProcesoDto
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.receso_dto import RecesoDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._construir_estimacion_input import (
    construir_estimacion_input,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    agrupar_por_equipo,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.services.estimacion.recesos import recesos_aplicables
from src.modules.contadores.domain.value_objects.estimacion.estimacion_input import EstimacionInput
from src.modules.contadores.domain.value_objects.estimacion.receso_cliente import RecesoCliente


class ConstructorEntradaSiges:
    def __init__(self, gateway: GrillaEstimacionPort, recesos_store: RecesosPort) -> None:
        self._gateway = gateway
        self._recesos_store = recesos_store

    async def fila(
        self, id_maquina: int, clase: str, solicitud: SolicitudRecalculoSigesDto
    ) -> FilaGrillaSigesDto | None:
        """La fila (`EquipoGrillaRaw`) del equipo/clase en la última grilla
        cargada. Sin `fresca`: reusa la grilla que ya cargó el tablero de ESE
        operador, como el legacy opera sobre la lista que tiene en pantalla."""
        filas = await self._gateway.fetch_grilla(
            solicitud.nro_proceso, solicitud.fecha_objetivo, operador=solicitud.operador
        )
        return next(
            (f for f in filas if f.id_maquina == id_maquina and str(f.id_clase_contador) == clase),
            None,
        )

    async def construir(
        self, id_maquina: int, clase: str, solicitud: SolicitudRecalculoSigesDto
    ) -> tuple[EstimacionInput, list[RecesoCliente]] | None:
        fila = await self.fila(id_maquina, clase, solicitud)
        if fila is None:
            return None
        equipo = agrupar_por_equipo([fila])[0]
        ctx = await contexto_proceso_siges(
            fila, solicitud.fecha_objetivo, solicitud.id_anexo, self._recesos_store
        )
        entrada = construir_estimacion_input(equipo, equipo.clases[0], ctx)
        recesos = recesos_aplicables(ctx.recesos, ctx.id_anexo, ctx.id_grupo_economico)
        return entrada, recesos


async def contexto_proceso_siges(
    fila: FilaGrillaSigesDto, fecha_objetivo: date, id_anexo: int, recesos_store: RecesosPort
) -> ContextoProcesoDto:
    """Recesos como el legacy (`ListarParaProcesoAsync` + `Receso.AplicaA`):
    los del anexo del proceso (aunque se hayan guardado con otro grupo) más
    los del grupo de la fila de Siges (`A.ID_GrupoE` del anexo del proceso,
    igual en todas las filas) — no el grupo elegido en el combo."""
    recesos = await recesos_store.listar_para_proceso(id_anexo, [fila.id_grupo_economico])
    return ContextoProcesoDto(
        fecha_objetivo=fecha_objetivo,
        periodo_desde=fila.periodo_desde,
        periodo_hasta=fila.periodo_hasta,
        id_grupo_economico=fila.id_grupo_economico,
        id_anexo=id_anexo,
        recesos=[_a_receso_cliente(r) for r in recesos],
    )


def _a_receso_cliente(r: RecesoDto) -> RecesoCliente:
    return RecesoCliente(r.fecha_desde, r.fecha_hasta, r.id_grupo_economico, r.id_anexo)

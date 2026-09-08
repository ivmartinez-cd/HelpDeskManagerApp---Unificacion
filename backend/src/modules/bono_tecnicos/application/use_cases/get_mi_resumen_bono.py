from collections import Counter

from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetMiResumenBonoRequest,
    GetPuntajesPeriodoRequest,
    MiResumenBonoDTO,
    PuntajeTecnicoDTO,
)
from src.modules.bono_tecnicos.application.use_cases.get_puntajes_periodo import (
    GetPuntajesPeriodo,
)
from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv
from src.modules.bono_tecnicos.domain.errors import TecnicoNoVinculadoError
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.bono_tecnicos.domain.repositories.tecnico_identity_gateway import (
    TecnicoIdentityGateway,
    TecnicoVinculado,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GetMiResumenBono:
    """El `PuntajeTecnicoDTO` del técnico autenticado (mismo cálculo que
    `GetPuntajesPeriodo`, filtrado al propio `id_tecnico`) + el desglose de
    sus TV por estado. Para el card "Mi bono" de Inicio y el detalle en
    Mis solicitudes de TV."""

    def __init__(
        self,
        identity_gateway: TecnicoIdentityGateway,
        get_puntajes_periodo: GetPuntajesPeriodo,
        solicitud_tv_repo: SolicitudTvRepository,
    ) -> None:
        self._identity_gateway = identity_gateway
        self._get_puntajes_periodo = get_puntajes_periodo
        self._solicitud_tv_repo = solicitud_tv_repo

    async def execute(self, request: GetMiResumenBonoRequest) -> MiResumenBonoDTO:
        vinculo = await self._identity_gateway.get_por_usuario(request.user_id)
        if vinculo is None:
            raise TecnicoNoVinculadoError(request.user_id)
        periodo = Periodo(request.periodo)
        puntajes = await self._get_puntajes_periodo.execute(
            GetPuntajesPeriodoRequest(periodo=request.periodo)
        )
        propio = next((p for p in puntajes if p.id_tecnico == vinculo.id_tecnico), None)
        solicitudes = await self._solicitud_tv_repo.list_by_periodo(
            periodo, id_tecnico=vinculo.id_tecnico
        )
        conteo_tv = Counter(s.estado for s in solicitudes)
        return _build_dto(vinculo, request.periodo, propio, conteo_tv)


def _build_dto(
    vinculo: TecnicoVinculado,
    periodo: int,
    propio: PuntajeTecnicoDTO | None,
    conteo_tv: Counter[EstadoSolicitudTv],
) -> MiResumenBonoDTO:
    base = propio or _sin_actividad(vinculo, periodo)
    return MiResumenBonoDTO(
        tecnico=base.tecnico,
        id_tecnico=base.id_tecnico,
        periodo=periodo,
        correctivo=base.correctivo,
        preventivo=base.preventivo,
        inst_des=base.inst_des,
        pre_correctivo=base.pre_correctivo,
        entrega_insumos=base.entrega_insumos,
        dias=base.dias,
        puntaje=base.puntaje,
        dias_sugeridos=base.dias_sugeridos,
        tv_aprobadas=conteo_tv.get(EstadoSolicitudTv.APROBADA, 0),
        tv_pendientes=conteo_tv.get(EstadoSolicitudTv.PENDIENTE, 0),
        tv_rechazadas=conteo_tv.get(EstadoSolicitudTv.RECHAZADA, 0),
    )


def _sin_actividad(vinculo: TecnicoVinculado, periodo: int) -> PuntajeTecnicoDTO:
    """`GetPuntajesPeriodo` solo incluye técnicos con algún incidente en el
    período (ver su docstring) — sin eso, el propio resumen igual tiene que
    devolver algo (en cero), no 404."""
    return PuntajeTecnicoDTO(
        tecnico=vinculo.tecnico,
        id_tecnico=vinculo.id_tecnico,
        periodo=periodo,
        correctivo=0,
        preventivo=0,
        inst_des=0,
        pre_correctivo=0,
        entrega_insumos=0,
        dias=0.0,
        tareas_varias=0,
        puntaje=None,
        dias_sugeridos=None,
    )

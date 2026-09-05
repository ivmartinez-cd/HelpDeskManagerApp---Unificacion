from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetPuntajesPeriodoRequest,
    PuntajeTecnicoDTO,
)
from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.repositories.bono_tecnico_input_repository import (
    BonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.domain.repositories.conteo_tecnico_gateway import (
    ConteoTecnicoGateway,
)
from src.modules.bono_tecnicos.domain.repositories.dias_sugeridos_gateway import (
    DiasSugeridosGateway,
)
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.bono_tecnicos.domain.services.calculador_puntaje import calcular_puntaje
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GetPuntajesPeriodo:
    """Resumen del bono de un período: conteos por categoría (consulta en
    vivo a Siges/MERCURIO, sin cache) + Días cargados a mano (Postgres propia)
    + Tareas Varias (cuenta de `SolicitudTv` APROBADA del período) + Puntaje
    calculado + Días sugeridos (a partir de las ausencias del empleado
    vinculado en Gestión de Personal, si lo hay — ver `dias_sugeridos_
    gateway`). Solo incluye técnicos con al menos un incidente de las 5
    categorías en el período — un técnico con Días cargados/TV aprobadas
    pero cero incidentes no tiene de dónde salir todavía (no existe un
    catálogo de técnicos propio, ver memoria de proyecto)."""

    def __init__(
        self,
        conteo_gateway: ConteoTecnicoGateway,
        input_repo: BonoTecnicoInputRepository,
        dias_sugeridos_gateway: DiasSugeridosGateway,
        solicitud_tv_repo: SolicitudTvRepository,
    ) -> None:
        self._conteo_gateway = conteo_gateway
        self._input_repo = input_repo
        self._dias_sugeridos_gateway = dias_sugeridos_gateway
        self._solicitud_tv_repo = solicitud_tv_repo

    async def execute(self, request: GetPuntajesPeriodoRequest) -> list[PuntajeTecnicoDTO]:
        periodo = Periodo(request.periodo)
        conteos = await self._conteo_gateway.find_conteos(periodo)
        inputs = await self._input_repo.find_by_periodo(periodo)
        inputs_por_tecnico = {i.id_tecnico: i for i in inputs}
        dias_sugeridos = await self._dias_sugeridos_gateway.get_dias_sugeridos_por_tecnico(
            periodo, [c.id_tecnico for c in conteos]
        )
        tv_aprobadas = await self._solicitud_tv_repo.count_aprobadas_por_tecnico(periodo)
        return [
            _build_dto(
                conteo,
                inputs_por_tecnico[conteo.id_tecnico].dias
                if conteo.id_tecnico in inputs_por_tecnico
                else 0,
                dias_sugeridos.get(conteo.id_tecnico),
                tv_aprobadas.get(conteo.id_tecnico, 0),
            )
            for conteo in conteos
        ]


def _build_dto(
    conteo: ConteoTecnico,
    dias: float,
    dias_sugeridos: float | None,
    tareas_varias: int,
) -> PuntajeTecnicoDTO:
    return PuntajeTecnicoDTO(
        tecnico=conteo.tecnico,
        id_tecnico=conteo.id_tecnico,
        periodo=conteo.periodo,
        correctivo=conteo.correctivo,
        preventivo=conteo.preventivo,
        inst_des=conteo.inst_des,
        pre_correctivo=conteo.pre_correctivo,
        entrega_insumos=conteo.entrega_insumos,
        dias=dias,
        tareas_varias=tareas_varias,
        puntaje=calcular_puntaje(conteo, dias, tareas_varias),
        dias_sugeridos=dias_sugeridos,
    )

from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GetPuntajesPeriodoRequest,
    PuntajeTecnicoDTO,
)
from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
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
from src.modules.bono_tecnicos.domain.services.calculador_puntaje import calcular_puntaje
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GetPuntajesPeriodo:
    """Resumen del bono de un período: conteos por categoría (consulta en
    vivo a Siges/MERCURIO, sin cache) + Días/Tareas Varias cargados a mano
    (Postgres propia) + Puntaje calculado + Días sugeridos (a partir de las
    ausencias del empleado vinculado en Gestión de Personal, si lo hay — ver
    `dias_sugeridos_gateway`). Solo incluye técnicos con al menos un
    incidente de las 5 categorías en el período — un técnico con Días/TV
    cargados pero cero incidentes no tiene de dónde salir todavía (no existe
    un catálogo de técnicos propio, ver memoria de proyecto)."""

    def __init__(
        self,
        conteo_gateway: ConteoTecnicoGateway,
        input_repo: BonoTecnicoInputRepository,
        dias_sugeridos_gateway: DiasSugeridosGateway,
    ) -> None:
        self._conteo_gateway = conteo_gateway
        self._input_repo = input_repo
        self._dias_sugeridos_gateway = dias_sugeridos_gateway

    async def execute(self, request: GetPuntajesPeriodoRequest) -> list[PuntajeTecnicoDTO]:
        periodo = Periodo(request.periodo)
        conteos = await self._conteo_gateway.find_conteos(periodo)
        inputs = await self._input_repo.find_by_periodo(periodo)
        inputs_por_tecnico = {i.id_tecnico: i for i in inputs}
        dias_sugeridos = await self._dias_sugeridos_gateway.get_dias_sugeridos_por_tecnico(
            periodo, [c.id_tecnico for c in conteos]
        )
        return [
            _build_dto(
                conteo,
                inputs_por_tecnico.get(conteo.id_tecnico),
                dias_sugeridos.get(conteo.id_tecnico),
            )
            for conteo in conteos
        ]


def _build_dto(
    conteo: ConteoTecnico, input_: BonoTecnicoInput | None, dias_sugeridos: int | None
) -> PuntajeTecnicoDTO:
    dias = input_.dias if input_ else 0
    tareas_varias = input_.tareas_varias if input_ else 0
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

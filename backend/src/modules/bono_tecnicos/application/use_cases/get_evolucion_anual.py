from dataclasses import dataclass

from src.modules.bono_tecnicos.application.dtos.evolucion_anual_dto import (
    EvolucionAnualDTO,
    EvolucionTecnicoDTO,
    GetEvolucionAnualRequest,
)
from src.modules.bono_tecnicos.domain.entities.conteo_tecnico import ConteoTecnico
from src.modules.bono_tecnicos.domain.repositories.bono_tecnico_input_repository import (
    BonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.domain.repositories.conteo_tecnico_gateway import (
    ConteoTecnicoGateway,
)
from src.modules.bono_tecnicos.domain.repositories.solicitud_tv_repository import (
    SolicitudTvRepository,
)
from src.modules.bono_tecnicos.domain.services.evolucion_anual import (
    PuntoMensual,
    promedio_equipo,
    serie_anual,
)
from src.modules.bono_tecnicos.domain.value_objects.conteo_tv import ConteoTv


@dataclass(frozen=True, slots=True)
class GetEvolucionAnualPorts:
    conteo_gateway: ConteoTecnicoGateway
    input_repo: BonoTecnicoInputRepository
    solicitud_tv_repo: SolicitudTvRepository


class GetEvolucionAnual:
    """Evolución mensual del año calendario pedido, por técnico y del
    promedio del equipo — vista de gerencia (`GET /evolucion-anual*`). No
    reemplaza el resumen operativo de un mes (`GetPuntajesPeriodo`): sigue
    siendo la fuente para cargar Días/TV del período en curso.

    Solo incluye técnicos con al menos un incidente en algún mes del año —
    mismo criterio y misma limitación que `GetPuntajesPeriodo` (no existe un
    catálogo propio de técnicos)."""

    def __init__(self, ports: GetEvolucionAnualPorts) -> None:
        self._ports = ports

    async def execute(self, request: GetEvolucionAnualRequest) -> EvolucionAnualDTO:
        anio = request.anio
        conteo_gateway = self._ports.conteo_gateway
        conteos = await conteo_gateway.find_conteos_anio(anio)
        inputs = await self._ports.input_repo.find_by_anio(anio)
        tv_repo = self._ports.solicitud_tv_repo
        tv_por_tecnico = await tv_repo.contar_por_tecnico_y_periodo(anio)

        nombres = {c.id_tecnico: c.tecnico for c in conteos}
        tecnicos = [
            _build_dto(
                id_tecnico,
                tecnico,
                serie_anual(
                    anio,
                    id_tecnico,
                    tecnico,
                    _de_tecnico(conteos, id_tecnico),
                    {i.periodo: i.dias for i in inputs if i.id_tecnico == id_tecnico},
                    _tv_de_tecnico(tv_por_tecnico, id_tecnico),
                ),
            )
            for id_tecnico, tecnico in nombres.items()
        ]
        return EvolucionAnualDTO(
            anio=anio,
            tecnicos=tecnicos,
            equipo=promedio_equipo([t.puntos for t in tecnicos]),
        )


def _de_tecnico(conteos: list[ConteoTecnico], id_tecnico: int) -> list[ConteoTecnico]:
    return [c for c in conteos if c.id_tecnico == id_tecnico]


def _tv_de_tecnico(
    tv_por_tecnico_y_periodo: dict[tuple[int, int], ConteoTv], id_tecnico: int
) -> dict[int, ConteoTv]:
    return {
        periodo: conteo
        for (id_t, periodo), conteo in tv_por_tecnico_y_periodo.items()
        if id_t == id_tecnico
    }


def _build_dto(id_tecnico: int, tecnico: str, puntos: list[PuntoMensual]) -> EvolucionTecnicoDTO:
    puntajes = [p.puntaje for p in puntos if p.puntaje is not None]
    return EvolucionTecnicoDTO(
        tecnico=tecnico,
        id_tecnico=id_tecnico,
        puntos=puntos,
        puntaje_promedio=round(sum(puntajes) / len(puntajes), 2) if puntajes else None,
        incidentes_total=int(sum(p.incidentes for p in puntos)),
        tv_solicitadas_total=int(sum(p.tv_solicitadas for p in puntos)),
        tv_aprobadas_total=int(sum(p.tv_aprobadas for p in puntos)),
    )

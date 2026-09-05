from dataclasses import dataclass

from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia


@dataclass(frozen=True, slots=True)
class CandidatosEquipoDto:
    id_maquina: int
    nro_serie: str
    empresa: str
    sucursal: str
    sector: str
    modelo: str
    tecnologia: Tecnologia
    velocidad_ppm: float | None
    lecturas: list[CandidatoLecturaDto]
    boxplot: BoxplotParqueDto | None

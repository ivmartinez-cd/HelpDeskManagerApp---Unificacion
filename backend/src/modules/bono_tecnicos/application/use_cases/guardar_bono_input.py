from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GuardarBonoInputRequest,
)
from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.repositories.bono_tecnico_input_repository import (
    BonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GuardarBonoInput:
    """Carga/corrige Días y Tareas Varias de un técnico en un período —
    reemplaza tipear a mano `Lista!$J$6`/`$J$7` en el Excel."""

    def __init__(self, repo: BonoTecnicoInputRepository) -> None:
        self._repo = repo

    async def execute(self, request: GuardarBonoInputRequest) -> None:
        Periodo(request.periodo)  # valida el formato AAAAMM, no se usa el resultado
        input_ = BonoTecnicoInput(
            id_tecnico=request.id_tecnico,
            periodo=request.periodo,
            tecnico=request.tecnico,
            dias=request.dias,
            tareas_varias=request.tareas_varias,
        )
        await self._repo.upsert(input_)

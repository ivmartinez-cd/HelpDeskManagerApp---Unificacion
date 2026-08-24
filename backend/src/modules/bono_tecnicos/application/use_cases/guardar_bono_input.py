from src.modules.bono_tecnicos.application.dtos.puntaje_tecnico_dto import (
    GuardarBonoInputRequest,
)
from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.repositories.bono_tecnico_input_repository import (
    BonoTecnicoInputRepository,
)
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class GuardarBonoInput:
    """Carga/corrige Días de un técnico en un período — reemplaza tipear a
    mano `Lista!$J$6` en el Excel. Tareas Varias (`$J$7`) ya no se carga acá:
    ver `CrearSolicitudTv`/`DecidirSolicitudTv`."""

    def __init__(self, repo: BonoTecnicoInputRepository) -> None:
        self._repo = repo

    async def execute(self, request: GuardarBonoInputRequest) -> None:
        Periodo(request.periodo)  # valida el formato AAAAMM, no se usa el resultado
        input_ = BonoTecnicoInput(
            id_tecnico=request.id_tecnico,
            periodo=request.periodo,
            tecnico=request.tecnico,
            dias=request.dias,
        )
        await self._repo.upsert(input_)

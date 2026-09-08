from typing import Protocol

from src.modules.bono_tecnicos.domain.entities.bono_tecnico_input import BonoTecnicoInput
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class BonoTecnicoInputRepository(Protocol):
    """Persistencia propia (Postgres) de Días/TV — Siges es de solo lectura,
    estos dos valores no tienen ninguna fuente ahí."""

    async def find_by_periodo(self, periodo: Periodo) -> list[BonoTecnicoInput]: ...

    async def find_by_anio(self, anio: int) -> list[BonoTecnicoInput]:
        """Los Días cargados de los 12 meses del año — para la evolución
        anual de gerencia, en vez de 12 `find_by_periodo`."""
        ...

    async def upsert(self, input_: BonoTecnicoInput) -> None: ...

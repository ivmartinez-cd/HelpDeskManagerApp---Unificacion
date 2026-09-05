from typing import Protocol

from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo


class DiasSugeridosGateway(Protocol):
    async def get_dias_sugeridos_por_tecnico(
        self, periodo: Periodo, ids_tecnico: list[int]
    ) -> dict[int, float]:
        """Días sugeridos por `id_tecnico` (días hábiles del período menos
        ausencias que reducen la jornada, ver `calculador_dias_sugeridos`)
        — solo para técnicos vinculados a un empleado de Gestión de
        Personal (`Empleado.siges_empresa_id`); los `id_tecnico` sin
        vínculo no aparecen en el resultado."""
        ...

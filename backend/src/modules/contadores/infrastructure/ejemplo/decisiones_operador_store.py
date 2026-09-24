"""Store en memoria de decisiones del operador del modo ejemplo — mismo
criterio temporal que `recesos_store.py`. Implementa `DecisionesOperadorPort`
(una decisión vigente por proceso, equipo y clase) con métodos `async def`
sin I/O real, para tratar ejemplo y real de forma uniforme — ver
`SqlAlchemyDecisionesOperadorRepository` para el modo real (Postgres)."""

from dataclasses import replace
from datetime import UTC, datetime
from functools import lru_cache

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
)

_Clave = tuple[int, int, str]


class DecisionesOperadorStore:
    def __init__(self) -> None:
        self._decisiones: dict[_Clave, DecisionOperadorDto] = {}

    async def listar_por_proceso(
        self, nro_proceso: int
    ) -> dict[tuple[int, str], DecisionOperadorDto]:
        return {
            (id_maquina, clase): decision
            for (proceso, id_maquina, clase), decision in self._decisiones.items()
            if proceso == nro_proceso
        }

    async def obtener(self, clave: ClaveDecisionDto) -> DecisionOperadorDto | None:
        return self._decisiones.get(_clave(clave))

    async def guardar(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        """Pisa la decisión de la fila ("último gana")."""
        self._decisiones[_clave(clave)] = replace(decision, actualizado_en=datetime.now(UTC))


def _clave(clave: ClaveDecisionDto) -> _Clave:
    return (clave.nro_proceso, clave.id_maquina, clave.clase)


@lru_cache
def get_decisiones_operador_store() -> DecisionesOperadorStore:
    return DecisionesOperadorStore()

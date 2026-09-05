"""Store en memoria de decisiones del operador del modo ejemplo (marcar
pendiente / agregar nota) — mismo criterio temporal que `recesos_store.py`.
Implementa `DecisionesOperadorPort` con métodos `async def` sin I/O real,
para tratar ejemplo y real de forma uniforme — ver
`SqlAlchemyDecisionesOperadorRepository` para el modo real (Postgres)."""

from functools import lru_cache

from src.modules.contadores.application.dtos.decision_operador_dto import DecisionOperadorDto


class DecisionesOperadorStore:
    def __init__(self) -> None:
        self._decisiones: dict[tuple[int, str], DecisionOperadorDto] = {}

    async def listar_todas(self) -> dict[tuple[int, str], DecisionOperadorDto]:
        return dict(self._decisiones)

    async def obtener(self, id_maquina: int, clase: str) -> DecisionOperadorDto | None:
        return self._decisiones.get((id_maquina, clase))

    async def marcar_pendiente(self, id_maquina: int, clase: str) -> None:
        actual = await self.obtener(id_maquina, clase) or DecisionOperadorDto()
        self._decisiones[(id_maquina, clase)] = DecisionOperadorDto(
            pendiente=True, nota=actual.nota
        )

    async def agregar_nota(self, id_maquina: int, clase: str, nota: str) -> None:
        actual = await self.obtener(id_maquina, clase) or DecisionOperadorDto()
        self._decisiones[(id_maquina, clase)] = DecisionOperadorDto(
            pendiente=actual.pendiente, nota=nota
        )

    async def aceptar(self, id_maquina: int, clase: str) -> None:
        self._decisiones.pop((id_maquina, clase), None)


@lru_cache
def get_decisiones_operador_store() -> DecisionesOperadorStore:
    return DecisionesOperadorStore()

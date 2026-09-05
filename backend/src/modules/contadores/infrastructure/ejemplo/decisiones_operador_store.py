"""Store en memoria de decisiones del operador sobre una fila (marcar
pendiente / agregar nota) — mismo criterio temporal que `recesos_store.py`:
se pierde al reiniciar, hoy vive en `Estim_Log` en el sistema original."""

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class DecisionOperador:
    pendiente: bool = False
    nota: str | None = None


class DecisionesOperadorStore:
    def __init__(self) -> None:
        self._decisiones: dict[tuple[int, str], DecisionOperador] = {}

    def obtener(self, id_maquina: int, clase: str) -> DecisionOperador | None:
        return self._decisiones.get((id_maquina, clase))

    def marcar_pendiente(self, id_maquina: int, clase: str) -> None:
        actual = self.obtener(id_maquina, clase) or DecisionOperador()
        self._decisiones[(id_maquina, clase)] = DecisionOperador(pendiente=True, nota=actual.nota)

    def agregar_nota(self, id_maquina: int, clase: str, nota: str) -> None:
        actual = self.obtener(id_maquina, clase) or DecisionOperador()
        self._decisiones[(id_maquina, clase)] = DecisionOperador(
            pendiente=actual.pendiente, nota=nota
        )

    def aceptar(self, id_maquina: int, clase: str) -> None:
        self._decisiones.pop((id_maquina, clase), None)


@lru_cache
def get_decisiones_operador_store() -> DecisionesOperadorStore:
    return DecisionesOperadorStore()

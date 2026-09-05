"""Store en memoria de recesos — TEMPORAL, se pierde al reiniciar el backend.
Alcanza para probar la UI con datos de ejemplo; el día que haya proceso real
esto pasa a ser una tabla propia (MODELO_DE_DATOS.md §5: `Estim_Recesos`)."""

from dataclasses import replace
from functools import lru_cache

from src.modules.contadores.application.dtos.receso_dto import RecesoDto


class RecesosEjemploStore:
    def __init__(self) -> None:
        self._recesos: list[RecesoDto] = []
        self._next_id = 1

    def listar(self, id_grupo_economico: int) -> list[RecesoDto]:
        return [r for r in self._recesos if r.id_grupo_economico == id_grupo_economico]

    def crear(self, receso_sin_id: RecesoDto) -> RecesoDto:
        receso = replace(receso_sin_id, id=self._next_id)
        self._next_id += 1
        self._recesos.append(receso)
        return receso

    def eliminar(self, id_receso: int) -> None:
        self._recesos = [r for r in self._recesos if r.id != id_receso]


@lru_cache
def get_recesos_ejemplo_store() -> RecesosEjemploStore:
    return RecesosEjemploStore()

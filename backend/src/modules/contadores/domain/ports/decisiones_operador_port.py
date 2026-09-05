from typing import Protocol

from src.modules.contadores.application.dtos.decision_operador_dto import DecisionOperadorDto


class DecisionesOperadorPort(Protocol):
    """Estado vigente (pendiente/nota) de la decisión del operador sobre una
    fila del tablero — complementa, no reemplaza, la auditoría append-only
    de `EstimLogPort` (esa es el historial completo; esta es solo el último
    estado, para no reconstruirlo del historial en cada carga del tablero).
    `listar_todas` existe para resolver el tablero completo con una sola
    consulta en vez de una por fila (evita N+1)."""

    async def listar_todas(self) -> dict[tuple[int, str], DecisionOperadorDto]: ...
    async def marcar_pendiente(self, id_maquina: int, clase: str) -> None: ...
    async def agregar_nota(self, id_maquina: int, clase: str, nota: str) -> None: ...
    async def aceptar(self, id_maquina: int, clase: str) -> None: ...

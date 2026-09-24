from typing import Protocol

from src.modules.contadores.application.dtos.decision_operador_dto import (
    ClaveDecisionDto,
    DecisionOperadorDto,
)


class DecisionesOperadorPort(Protocol):
    """Decisión vigente del operador por (proceso, equipo, clase) — complementa,
    no reemplaza, la auditoría append-only de `EstimLogPort` (esa es el
    historial completo; esta es solo la última acción de cada fila, lo que el
    legacy obtiene con `GetUltimasDecisionesProcesoAsync`). `listar_por_proceso`
    resuelve el tablero completo con una sola consulta (evita N+1)."""

    async def listar_por_proceso(
        self, nro_proceso: int
    ) -> dict[tuple[int, str], DecisionOperadorDto]:
        """Clave del dict: (id_maquina, clase)."""
        ...

    async def obtener(self, clave: ClaveDecisionDto) -> DecisionOperadorDto | None:
        """La decisión vigente de una sola fila (la que el panel está
        mostrando: `EquipoEfectivo` del legacy)."""
        ...

    async def guardar(self, clave: ClaveDecisionDto, decision: DecisionOperadorDto) -> None:
        """Pisa la decisión vigente de esa fila ("último gana", como
        `Estim_Log` del legacy)."""
        ...

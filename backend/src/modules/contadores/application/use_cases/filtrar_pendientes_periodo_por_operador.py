"""Recorta el arrastre real de Siges (`ClientesPendientesPeriodo`, todos los
grupos económicos del país) a solo los clientes de la cartera del operador
que mira la card de Inicio — misma visibilidad que `GetPendingClientsUseCase`:
el superadmin ve todo, un operador regular solo lo suyo."""

from dataclasses import replace
from datetime import date, timedelta

from src.modules.contadores.domain.entities.clientes_pendientes_periodo import (
    ClientesPendientesPeriodo,
)
from src.modules.contadores.domain.repositories.calendar_event_repository import (
    CalendarEventRepository,
)
from src.modules.contadores.domain.services.cliente_matcher import (
    ALIAS_CLIENTE_GRUPO_NORM,
    IndiceNombres,
    buscar_por_nombre,
    normalizar_nombre,
)


class FiltrarPendientesPeriodoPorOperador:
    def __init__(self, repository: CalendarEventRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        resultado: ClientesPendientesPeriodo,
        *,
        is_superadmin: bool,
        full_name: str,
        hoy: date,
        dias_ventana: int,
    ) -> ClientesPendientesPeriodo:
        if is_superadmin or not resultado.grupos:
            return resultado
        operador = await self._repository.find_operador_by_nombre(full_name)
        if operador is None:
            return replace(resultado, grupos=())
        clientes = await self._clientes_operador(operador.id, hoy, dias_ventana)
        indice = self._indice(clientes)
        grupos = tuple(g for g in resultado.grupos if buscar_por_nombre(g, indice) is not None)
        return replace(resultado, grupos=grupos)

    async def _clientes_operador(
        self, operador_id: str, hoy: date, dias_ventana: int
    ) -> set[str]:
        events = await self._repository.list_events(
            start_date=hoy.isoformat(),
            end_date=(hoy + timedelta(days=dias_ventana)).isoformat(),
            operador_id=operador_id,
        )
        return {e.cliente for e in events if e.cliente}

    @staticmethod
    def _indice(clientes: set[str]) -> IndiceNombres[bool]:
        directo = {normalizar_nombre(c): True for c in clientes}
        via_alias = {
            ALIAS_CLIENTE_GRUPO_NORM[normalizar_nombre(c)]: True
            for c in clientes
            if normalizar_nombre(c) in ALIAS_CLIENTE_GRUPO_NORM
        }
        return IndiceNombres({**directo, **via_alias})

from datetime import date

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.use_cases.get_pending_clients import (
    GetPendingClientsUseCase,
)
from src.modules.contadores.domain.services.ciclo_cierre import ventana_periodo_actual


class GetClientesPendientesPeriodoActualUseCase:
    """Card de Inicio: clientes del período de facturación EN CURSO (ventana
    real, ver `ventana_periodo_actual`) que todavía siguen en el calendario
    de Gestión — a diferencia de `GetPendingClientsUseCase` (solo atraso ya
    vencido), acá entran también los que todavía no llegaron a su fecha:
    mientras Gestión no saque el evento del calendario, ese cliente sigue sin
    cerrar para este período. Un cliente por fila (el primero por fecha si
    tiene más de un evento en la ventana). A propósito NO cruza contra Siges
    (`FiltrarPendientesPorPeriodoReal` mide arrastre de períodos ANTERIORES
    al actual — `PeriodoFacturacion < período_actual` en
    `estado_cierre_grupos_query.py` — no si el período en curso está
    cerrado; aplicarlo acá excluiría clientes sin deuda vieja aunque su
    evento de este período siga en el calendario)."""

    def __init__(self, pending: GetPendingClientsUseCase) -> None:
        self._pending = pending

    async def execute(
        self,
        *,
        is_superadmin: bool,
        full_name: str,
        today: date,
        exclude_operador_ids: frozenset[str] = frozenset(),
    ) -> list[CalendarEventAnotado]:
        inicio, fin = ventana_periodo_actual(today)
        anotados = await self._pending.execute(
            is_superadmin=is_superadmin,
            full_name=full_name,
            today=today,
            cutoff_days=0,  # ignorado: la ventana la fijan start_date/end_date
            exclude_operador_ids=exclude_operador_ids,
            start_date=inicio.isoformat(),
            end_date=fin.isoformat(),
        )
        return _dedup_por_cliente(anotados)


def _dedup_por_cliente(anotados: list[CalendarEventAnotado]) -> list[CalendarEventAnotado]:
    vistos: set[str] = set()
    resultado = []
    for anotado in anotados:
        cliente = anotado.event.cliente
        if not cliente or cliente in vistos:
            continue
        vistos.add(cliente)
        resultado.append(anotado)
    return resultado

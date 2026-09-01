from datetime import UTC, date, datetime

import pytest

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.use_cases.listar_anexos_sin_procesar import (
    ListarAnexosSinProcesar,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.estado_proceso_anexo import (
    EstadoProcesoAnexo,
    EstadoProcesoAnexosSnapshot,
)
from src.shared.domain.errors import ExternalServiceError

_CONSULTADO_EN = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
# periodo_de(hoy)="202608", periodo_anterior="202607": un mes de gracia.
_HOY = date(2026, 8, 31)


class _FakePort:
    def __init__(
        self, anexos: list[EstadoProcesoAnexo] | None = None, *, falla: bool = False
    ) -> None:
        self._anexos = anexos or []
        self._falla = falla

    async def list_estado(
        self, *, force_refresh: bool = False
    ) -> EstadoProcesoAnexosSnapshot:
        if self._falla:
            raise ExternalServiceError("Siges caído")
        return EstadoProcesoAnexosSnapshot(anexos=self._anexos, consultado_en=_CONSULTADO_EN)


def _pendiente(id_: str, cliente: str | None, *, start: str = "2026-08-12") -> CalendarEventAnotado:
    return CalendarEventAnotado(
        event=CalendarEvent(id=id_, title="X", start=f"{start}T00:00:00-03:00", cliente=cliente),
        cobertura=None,
    )


def _anexo(grupo: str, ultimo: str | None, *, id_anexo: int = 1) -> EstadoProcesoAnexo:
    return EstadoProcesoAnexo(
        id_anexo=id_anexo, anexo="COD1/A", grupo=grupo, ultimo_periodo_procesado=ultimo
    )


@pytest.mark.asyncio
async def test_backlog_vacio_no_consulta_el_puerto() -> None:
    port = _FakePort(falla=True)
    resultado = await ListarAnexosSinProcesar(port).execute([], hoy=_HOY)
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_anexo_con_ultimo_periodo_viejo_se_cuenta() -> None:
    port = _FakePort([_anexo("Sika", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika")], hoy=_HOY
    )
    assert [a.grupo for a in resultado.anexos] == ["Sika"]


@pytest.mark.asyncio
async def test_anexo_ya_procesado_del_periodo_esperado_no_se_cuenta() -> None:
    port = _FakePort([_anexo("Sika", "202607")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika")], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_anexo_que_ya_rodo_a_un_periodo_posterior_no_se_cuenta() -> None:
    port = _FakePort([_anexo("Sika", "202608")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika")], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_grupo_sin_evento_vencido_no_se_cuenta() -> None:
    """El universo del KPI lo define el calendario, no Siges: un anexo sin
    proceso de un cliente sin backlog no es un olvido detectable."""
    port = _FakePort([_anexo("Otro Cliente Sin Backlog", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika")], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_cliente_sin_cruce_de_nombre_no_se_cuenta() -> None:
    """Inversión a propósito de FiltrarPendientesPorPeriodoReal: acá un
    falso positivo (acusar a alguien sin certeza) es peor que uno negativo."""
    port = _FakePort([_anexo("Un Grupo Totalmente Distinto SA", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Roemmers")], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_anexo_sin_historial_de_proceso_no_se_cuenta() -> None:
    """Sin historial no hay prueba de olvido: puede ser un alta reciente o
    un anexo que factura por otro circuito."""
    port = _FakePort([_anexo("Sika", None)])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika")], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_cruza_por_alias_manual() -> None:
    port = _FakePort([_anexo("JBS Leather Argentina S.A.", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "JBS")], hoy=_HOY
    )
    assert [a.grupo for a in resultado.anexos] == ["JBS Leather Argentina S.A."]


@pytest.mark.asyncio
async def test_cruza_por_separadores_equivalentes() -> None:
    port = _FakePort([_anexo("Roemmers - Maprimed", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Roemmers / Maprimed")], hoy=_HOY
    )
    assert [a.grupo for a in resultado.anexos] == ["Roemmers - Maprimed"]


@pytest.mark.asyncio
async def test_varios_eventos_vencidos_usan_el_mas_antiguo_para_mostrar() -> None:
    """El más antiguo (mayor dias_vencido) es la señal más fuerte de hace
    cuánto viene el arrastre — no cambia si se cuenta o no, solo qué fecha
    se muestra en el detalle."""
    port = _FakePort([_anexo("Sika", "202606")])
    pendientes = [
        _pendiente("e1", "Sika", start="2026-08-25"),
        _pendiente("e2", "Sika", start="2026-08-05"),
    ]
    resultado = await ListarAnexosSinProcesar(port).execute(pendientes, hoy=_HOY)
    assert resultado.anexos[0].fecha_evento == "2026-08-05"
    assert resultado.anexos[0].dias_vencido == 26


@pytest.mark.asyncio
async def test_siges_caido_propaga_sin_devolver_cero() -> None:
    port = _FakePort(falla=True)
    with pytest.raises(ExternalServiceError):
        await ListarAnexosSinProcesar(port).execute([_pendiente("e1", "Sika")], hoy=_HOY)


@pytest.mark.asyncio
async def test_evento_sin_cliente_se_ignora() -> None:
    port = _FakePort([_anexo("Sika", "202606")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", None)], hoy=_HOY
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_ordena_por_dias_vencido_descendente() -> None:
    port = _FakePort([_anexo("Sika", "202606", id_anexo=1), _anexo("Opdea", "202606", id_anexo=2)])
    pendientes = [
        _pendiente("e1", "Sika", start="2026-08-25"),
        _pendiente("e2", "Opdea", start="2026-08-05"),
    ]
    resultado = await ListarAnexosSinProcesar(port).execute(pendientes, hoy=_HOY)
    assert [a.grupo for a in resultado.anexos] == ["Opdea", "Sika"]

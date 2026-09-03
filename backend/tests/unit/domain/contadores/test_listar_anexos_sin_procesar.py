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
# El período esperado sale de la fecha de cada evento (ciclo del día 20), no
# de `hoy`: el evento default del 12/8 pide "202607"; uno posterior al 20/8
# pide "202608".
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


def _anexo(
    grupo: str, ultimo: str | None, *, id_anexo: int = 1, maquinas_activas: int = 1
) -> EstadoProcesoAnexo:
    return EstadoProcesoAnexo(
        id_anexo=id_anexo,
        anexo="COD1/A",
        grupo=grupo,
        ultimo_periodo_procesado=ultimo,
        maquinas_activas=maquinas_activas,
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
async def test_evento_posterior_al_dia_20_exige_el_periodo_que_arranco_ese_dia() -> None:
    """Caso real del 2026-09-03: visita del 28/8 vencida y el anexo con
    último proceso 202607 — el período que se estaba procesando era 202608."""
    port = _FakePort([_anexo("Oca", "202607")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Oca", start="2026-08-28")], hoy=date(2026, 9, 3)
    )
    assert [(a.periodo_esperado, a.dias_vencido) for a in resultado.anexos] == [("202608", 6)]


@pytest.mark.asyncio
async def test_evento_anterior_al_dia_20_no_exige_el_periodo_nuevo() -> None:
    """La ventana de backlog cruza el día 20: una visita del 12/8 pertenece al
    ciclo 202607 y no acusa por 202608 aunque hoy ya sea septiembre."""
    port = _FakePort([_anexo("Sika", "202607")])
    resultado = await ListarAnexosSinProcesar(port).execute(
        [_pendiente("e1", "Sika", start="2026-08-12")], hoy=date(2026, 9, 3)
    )
    assert resultado.anexos == []


@pytest.mark.asyncio
async def test_varios_eventos_exigen_el_periodo_mas_nuevo_y_muestran_el_mas_antiguo() -> None:
    port = _FakePort([_anexo("Sika", "202607")])
    pendientes = [
        _pendiente("e1", "Sika", start="2026-08-12"),
        _pendiente("e2", "Sika", start="2026-08-28"),
    ]
    resultado = await ListarAnexosSinProcesar(port).execute(pendientes, hoy=date(2026, 9, 3))
    assert [(a.periodo_esperado, a.fecha_evento) for a in resultado.anexos] == [
        ("202608", "2026-08-12")
    ]


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
async def test_anexo_sin_maquinas_activas_no_se_cuenta() -> None:
    """Caso real 2026-09-03: OCA (COD36CDSI00619/A) tiene 12 máquinas
    ligadas, las 12 'De Baja' — sin parque vigente no hay nada que
    facturar, no es un olvido del operador."""
    port = _FakePort([_anexo("Sika", "202606", maquinas_activas=0)])
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

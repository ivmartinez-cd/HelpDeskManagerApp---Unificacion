from datetime import UTC, datetime

import pytest

from src.modules.contadores.application.dtos.calendar_event_anotado import CalendarEventAnotado
from src.modules.contadores.application.use_cases.filtrar_pendientes_por_periodo_real import (
    FiltrarPendientesPorPeriodoReal,
)
from src.modules.contadores.domain.entities.calendar_event import CalendarEvent
from src.modules.contadores.domain.entities.estado_cierre_grupo import (
    EstadoCierreGrupo,
    EstadoCierreGruposSnapshot,
)
from src.shared.domain.errors import ExternalServiceError

_CONSULTADO_EN = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


class _FakePort:
    def __init__(
        self, grupos: list[EstadoCierreGrupo] | None = None, *, falla: bool = False
    ) -> None:
        self._grupos = grupos or []
        self._falla = falla

    async def list_estado(self, *, force_refresh: bool = False) -> EstadoCierreGruposSnapshot:
        if self._falla:
            raise ExternalServiceError("Siges caído")
        return EstadoCierreGruposSnapshot(grupos=self._grupos, consultado_en=_CONSULTADO_EN)


def _pendiente(id_: str, cliente: str | None) -> CalendarEventAnotado:
    return CalendarEventAnotado(
        event=CalendarEvent(id=id_, title="X", start="2026-08-14T00:00:00-03:00", cliente=cliente),
        cobertura=None,
    )


@pytest.mark.asyncio
async def test_lista_vacia_no_consulta_el_puerto() -> None:
    port = _FakePort()
    result = await FiltrarPendientesPorPeriodoReal(port).execute([])
    assert result == []


@pytest.mark.asyncio
async def test_cliente_con_periodo_todavia_abierto_se_conserva() -> None:
    port = _FakePort([EstadoCierreGrupo(grupo="Sika", sin_cerrar=True)])
    pendiente = _pendiente("e1", "Sika")
    result = await FiltrarPendientesPorPeriodoReal(port).execute([pendiente])
    assert result == [pendiente]


@pytest.mark.asyncio
async def test_cliente_ya_facturado_o_rodado_al_mes_en_curso_se_excluye() -> None:
    port = _FakePort([EstadoCierreGrupo(grupo="Sika", sin_cerrar=False)])
    result = await FiltrarPendientesPorPeriodoReal(port).execute([_pendiente("e1", "Sika")])
    assert result == []


@pytest.mark.asyncio
async def test_cliente_sin_anexo_de_impresion_se_conserva_sin_certeza() -> None:
    """No hay match en Siges (cliente de servicios, no de Impresión, o nombre
    no cruza): no hay señal para descartarlo, se mantiene."""
    port = _FakePort([EstadoCierreGrupo(grupo="Otro Cliente", sin_cerrar=False)])
    pendiente = _pendiente("e1", "Roemmers / Maprimed")
    result = await FiltrarPendientesPorPeriodoReal(port).execute([pendiente])
    assert result == [pendiente]


@pytest.mark.asyncio
async def test_siges_caido_degrada_a_no_filtrar() -> None:
    port = _FakePort(falla=True)
    pendientes = [_pendiente("e1", "Sika"), _pendiente("e2", "Opdea")]
    result = await FiltrarPendientesPorPeriodoReal(port).execute(pendientes)
    assert result == pendientes


@pytest.mark.asyncio
async def test_cruza_por_grupo_normalizado_con_separadores_equivalentes() -> None:
    port = _FakePort([EstadoCierreGrupo(grupo="Roemmers - Maprimed", sin_cerrar=True)])
    pendiente = _pendiente("e1", "Roemmers / Maprimed")
    result = await FiltrarPendientesPorPeriodoReal(port).execute([pendiente])
    assert result == [pendiente]


class TestAliasManual:
    """Siglas/abreviaturas que el cruce automático no resuelve (muy cortas
    para contención, o sin prefijo tokenizado común) tienen alias manual."""

    @pytest.mark.asyncio
    async def test_sigla_corta_con_alias_ya_cerrada_se_excluye(self) -> None:
        port = _FakePort(
            [EstadoCierreGrupo(grupo="JBS Leather Argentina S.A.", sin_cerrar=False)]
        )
        result = await FiltrarPendientesPorPeriodoReal(port).execute([_pendiente("e1", "JBS")])
        assert result == []

    @pytest.mark.asyncio
    async def test_sigla_corta_con_alias_todavia_abierta_se_conserva(self) -> None:
        port = _FakePort([EstadoCierreGrupo(grupo="Arag S.R.L.", sin_cerrar=True)])
        pendiente = _pendiente("e1", "Arag")
        result = await FiltrarPendientesPorPeriodoReal(port).execute([pendiente])
        assert result == [pendiente]

    @pytest.mark.asyncio
    async def test_abreviatura_sin_prefijo_comun_usa_alias(self) -> None:
        port = _FakePort(
            [EstadoCierreGrupo(grupo="Hospital Italiano De La Plata", sin_cerrar=False)]
        )
        result = await FiltrarPendientesPorPeriodoReal(port).execute(
            [_pendiente("e1", "HOSP. ITALIANO DE LA PLATA")]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_nombre_sin_prefijo_comun_usa_alias_instituto_poveda(self) -> None:
        """'Instituto Poveda' (Gestión) vs 'Institución Cultural Femenina'
        (Siges) no comparten ni prefijo ni contención — sin alias quedaba
        siempre "sin cruce" y el backlog lo mostraba de arrastre eterno."""
        port = _FakePort(
            [EstadoCierreGrupo(grupo="Institución Cultural Femenina", sin_cerrar=False)]
        )
        result = await FiltrarPendientesPorPeriodoReal(port).execute(
            [_pendiente("e1", "Instituto Poveda")]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_sin_espacio_en_siges_usa_alias_axion_log(self) -> None:
        """'Axion Log' (Gestión) vs 'AxionLog' (Siges, sin espacio) no
        cruzan por contención porque el espacio rompe la subcadena."""
        port = _FakePort([EstadoCierreGrupo(grupo="AxionLog", sin_cerrar=False)])
        result = await FiltrarPendientesPorPeriodoReal(port).execute(
            [_pendiente("e1", "Axion Log")]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_sigla_corta_usa_alias_eana(self) -> None:
        port = _FakePort([EstadoCierreGrupo(grupo="EANA SE", sin_cerrar=False)])
        result = await FiltrarPendientesPorPeriodoReal(port).execute([_pendiente("e1", "EANA")])
        assert result == []

    @pytest.mark.asyncio
    async def test_nombre_mas_corto_en_gestion_usa_alias_froneri(self) -> None:
        """'Froneri S. A.' (Gestión) vs 'Froneri Argentina S. A.' (Siges) no
        cruzan por contención: 'Argentina' rompe la subcadena en el medio."""
        port = _FakePort(
            [EstadoCierreGrupo(grupo="Froneri Argentina S. A.", sin_cerrar=False)]
        )
        result = await FiltrarPendientesPorPeriodoReal(port).execute(
            [_pendiente("e1", "Froneri S. A.")]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_sigla_corta_usa_alias_gire(self) -> None:
        port = _FakePort([EstadoCierreGrupo(grupo="GIRE S.A.", sin_cerrar=False)])
        result = await FiltrarPendientesPorPeriodoReal(port).execute([_pendiente("e1", "GIRE")])
        assert result == []

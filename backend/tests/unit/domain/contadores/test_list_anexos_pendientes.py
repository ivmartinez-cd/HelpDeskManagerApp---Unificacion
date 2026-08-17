from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.modules.contadores.application.dtos.equipo_sin_real_anotado import OperadorAsignado
from src.modules.contadores.application.dtos.list_anexos_pendientes_request import (
    ListAnexosPendientesRequest,
)
from src.modules.contadores.application.use_cases.get_anexos_pendientes_resumen import (
    GetAnexosPendientesResumenUseCase,
)
from src.modules.contadores.application.use_cases.list_anexos_pendientes import (
    ListAnexosPendientesUseCase,
    _buscar_operador,
    _IndiceOperadores,
)
from src.modules.contadores.domain.entities.anexo_pendiente import (
    AnexoPendiente,
    AnexosPendientesSnapshot,
)
from src.modules.contadores.domain.services.cliente_matcher import normalizar_nombre
from src.modules.contadores.domain.services.periodos_facturacion import (
    estado_de_periodo,
    periodo_anterior,
    periodo_de,
    restar_meses,
)

_CONSULTADO_EN = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
_HOY = date(2026, 8, 14)


def _anexo(
    nombre: str,
    periodo: str,
    *,
    grupo: str | None = "Calico",
    vendedor: str | None = "Soledad Miguez",
    importe: str = "0",
) -> AnexoPendiente:
    return AnexoPendiente(
        id_anexo=abs(hash(nombre)) % 100000,
        anexo=nombre,
        grupo=grupo,
        contrato="COD36CDSI00328",
        id_empresa_admin=3,
        empresa_admin="CD3 (CDSISA)",
        vendedor=vendedor,
        moneda="Pesos",
        moneda_facturacion="Pesos",
        periodo=periodo,
        fecha_proceso=date(2026, 8, 7),
        importe_usd=Decimal(importe),
    )


class _FakePort:
    def __init__(self, anexos: list[AnexoPendiente]) -> None:
        self._anexos = anexos
        self.refresh_calls: list[bool] = []

    async def list_anexos(self, *, force_refresh: bool = False) -> AnexosPendientesSnapshot:
        self.refresh_calls.append(force_refresh)
        return AnexosPendientesSnapshot(anexos=self._anexos, consultado_en=_CONSULTADO_EN)


_UNIVERSO = [
    _anexo("COD36CDSI00328/A7", "202607"),
    _anexo("SUMCDSI0077/C2", "202607", grupo="Roemmers - Maprimed", importe="6472.41"),
    _anexo("COD36CDSI00674/A1", "202606", grupo="Galicia Seguros"),
    _anexo("COD30CDSI00510/A1/C1", "202412", grupo="Chubb", vendedor="Barbara Romero"),
]


def test_periodo_de_y_anterior() -> None:
    assert periodo_de(_HOY) == "202608"
    assert periodo_anterior("202608") == "202607"
    assert periodo_anterior("202601") == "202512"


def test_restar_meses_cruza_el_anio() -> None:
    assert restar_meses(date(2026, 8, 14), 12) == date(2025, 8, 1)
    assert restar_meses(date(2026, 3, 31), 6) == date(2025, 9, 1)


def test_estado_mes_anterior_en_proceso_y_mas_viejo_demorado() -> None:
    # Regla de la TL: 202607 EN PROCESO, 202606 (y anteriores) DEMORADO.
    assert estado_de_periodo("202607", hoy=_HOY) == "en_proceso"
    assert estado_de_periodo("202606", hoy=_HOY) == "demorado"
    assert estado_de_periodo("202412", hoy=_HOY) == "demorado"


@pytest.mark.asyncio
async def test_anota_estado_y_conserva_el_orden_del_snapshot() -> None:
    result = await ListAnexosPendientesUseCase(_FakePort(_UNIVERSO)).execute(
        ListAnexosPendientesRequest(), hoy=_HOY
    )
    assert [a.anexo.anexo for a in result.anexos] == [a.anexo for a in _UNIVERSO]
    estados = {a.anexo.anexo: a.estado for a in result.anexos}
    assert estados["COD36CDSI00328/A7"] == "en_proceso"
    assert estados["COD36CDSI00674/A1"] == "demorado"
    assert result.consultado_en == _CONSULTADO_EN


@pytest.mark.asyncio
async def test_filtra_por_estado_y_busqueda() -> None:
    use_case = ListAnexosPendientesUseCase(_FakePort(_UNIVERSO))
    demorados = await use_case.execute(
        ListAnexosPendientesRequest(estado="demorado"), hoy=_HOY
    )
    assert {a.anexo.anexo for a in demorados.anexos} == {
        "COD36CDSI00674/A1",
        "COD30CDSI00510/A1/C1",
    }
    por_grupo = await use_case.execute(ListAnexosPendientesRequest(search="roemmers"))
    assert [a.anexo.anexo for a in por_grupo.anexos] == ["SUMCDSI0077/C2"]
    por_vendedor = await use_case.execute(ListAnexosPendientesRequest(search="barbara"))
    assert [a.anexo.anexo for a in por_vendedor.anexos] == ["COD30CDSI00510/A1/C1"]


@pytest.mark.asyncio
async def test_force_refresh_llega_al_puerto() -> None:
    port = _FakePort(_UNIVERSO)
    await ListAnexosPendientesUseCase(port).execute(
        ListAnexosPendientesRequest(force_refresh=True)
    )
    assert port.refresh_calls == [True]


@pytest.mark.asyncio
async def test_resumen_cuenta_estados_y_suma_importes() -> None:
    resumen = await GetAnexosPendientesResumenUseCase(_FakePort(_UNIVERSO)).execute(
        hoy=_HOY
    )
    assert resumen.total == 4
    assert resumen.en_proceso == 2
    assert resumen.demorados == 2
    assert resumen.importe_usd_total == Decimal("6472.41")
    assert resumen.periodo_referencia == "202607"
    assert resumen.consultado_en == _CONSULTADO_EN


class TestBuscarOperador:
    """Cruce grupo del anexo → operador: exacto > flex (separadores) >
    contención única; ambiguo o corto queda sin operador."""

    def _indice(self, nombres: dict[str, str]) -> _IndiceOperadores:
        return _IndiceOperadores(
            {
                normalizar_nombre(k): OperadorAsignado(nombre=v, color=None)
                for k, v in nombres.items()
            }
        )

    def test_match_exacto(self) -> None:
        indice = self._indice({"Chubb": "Barbara Romero"})
        op = _buscar_operador("Chubb", indice)
        assert op is not None and op.nombre == "Barbara Romero"

    def test_flex_equipara_separadores(self) -> None:
        indice = self._indice({"Roemmers / Maprimed": "Soledad Miguez"})
        op = _buscar_operador("Roemmers - Maprimed", indice)
        assert op is not None and op.nombre == "Soledad Miguez"

    def test_contencion_unica(self) -> None:
        indice = self._indice({"Galicia Seguros Retiro": "Op A", "Chubb": "Op B"})
        op = _buscar_operador("Galicia Seguros", indice)
        assert op is not None and op.nombre == "Op A"

    def test_contencion_ambigua_queda_sin_operador(self) -> None:
        indice = self._indice({"Galicia Seguros": "Op A", "Galicia Retiro": "Op B"})
        assert _buscar_operador("Galicia", indice) is None

    def test_nombre_corto_no_matchea_por_contencion(self) -> None:
        indice = self._indice({"ASP Logistica Central": "Op A"})
        assert _buscar_operador("ASP", indice) is None

    def test_sin_grupo_o_sin_mapa(self) -> None:
        assert _buscar_operador(None, self._indice({"Chubb": "Op"})) is None
        assert _buscar_operador("Chubb", self._indice({})) is None

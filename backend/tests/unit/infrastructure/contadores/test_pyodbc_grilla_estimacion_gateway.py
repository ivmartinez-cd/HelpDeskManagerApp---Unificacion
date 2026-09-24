"""PyodbcGrillaEstimacionGateway con un runner fake: mapeo posicional igual a
`SiGesRepository.GetGrillaAsync` del legacy (histórico H11..H01, fecha/tipo
del contador actual, NULL → default sin tirar la grilla) y la política de
carga: el tablero consulta fresco, el resto reusa la última grilla."""

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from src.modules.contadores.infrastructure.siges import pyodbc_grilla_estimacion_gateway as mod
from src.modules.contadores.infrastructure.siges.pyodbc_grilla_estimacion_gateway import (
    PyodbcGrillaEstimacionGateway,
)

_FECHA = date(2026, 4, 30)


class FakeRunner:
    def __init__(self, filas: list[list[Any]]) -> None:
        self.filas = filas
        self.llamadas: list[tuple[object, ...]] = []

    async def fetch_all(self, sql: str, params: Sequence[object] = (), **_: Any) -> list[Any]:
        self.llamadas.append(tuple(params))
        return [list(f) for f in self.filas]


def _fila_cruda(**columnas: Any) -> list[Any]:
    """74 columnas con valores mínimos válidos; `c<N>=valor` pisa la N."""
    fila: list[Any] = [None] * 74
    fila[0:7] = [101, 10, "SER1", 5, "Empresa", 7, "Sucursal"]
    fila[9:13] = [900, 55, "Modelo X", 1]
    fila[14] = True
    fila[36:38] = [datetime(2026, 5, 1), datetime(2026, 4, 1)]
    fila[38] = 1
    fila[56] = 1
    fila[40:51] = [float(i) for i in range(1, 12)]  # H01=1 … H11=11
    for clave, valor in columnas.items():
        fila[int(clave[1:])] = valor
    return fila


async def _una_fila(**columnas: Any) -> Any:
    gateway = PyodbcGrillaEstimacionGateway(FakeRunner([_fila_cruda(**columnas)]))  # type: ignore[arg-type]
    return (await gateway.fetch_grilla(1, _FECHA))[0]


async def test_historico_va_de_h11_a_h01_viejo_a_reciente_como_historico11() -> None:
    fila = await _una_fila()

    assert fila.historico == (11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0)


async def test_historico_null_se_lee_como_cero() -> None:
    fila = await _una_fila(c40=None, c50=None)

    assert fila.historico[0] == 0.0 and fila.historico[-1] == 0.0


async def test_fila_real_trae_fecha_y_tipo_del_contador_actual_e_impresiones_reales() -> None:
    fila = await _una_fila(
        c14=False, c51=122_300, c52=datetime(2026, 4, 28), c53=22, c54=3_800
    )

    assert fila.fc_impre_contador_actual == 122_300.0
    assert fila.fc_fecha_cont_actual == date(2026, 4, 28)
    assert fila.fc_tipo_toma_cont_actual == 22
    assert fila.fc_impresiones_reales == 3_800.0


async def test_estado_y_modo_oper_null_se_leen_como_cero_sin_tirar_la_grilla() -> None:
    fila = await _una_fila(c38=None, c39=None, c56=None)

    assert fila.id_estado_maquina == 0
    assert fila.estado_maquina_desc == ""
    assert fila.id_modo_oper == 0


async def test_textos_null_se_leen_como_cadena_vacia_no_como_none() -> None:
    fila = await _una_fila(c2=None, c4=None, c6=None, c11=None)

    assert (fila.nro_serie, fila.empresa_desc, fila.sucursal_desc, fila.modelo_desc) == (
        "", "", "", ""
    )


async def test_contador_anterior_null_queda_none() -> None:
    fila = await _una_fila(c15=None, c16=None, c17=None)

    assert fila.contador_anterior_valor is None
    assert fila.contador_anterior_fecha is None
    assert fila.contador_anterior_tipo_toma is None


async def test_carga_fresca_siempre_consulta_siges() -> None:
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]

    await gateway.fetch_grilla(7, _FECHA, fresca=True)
    await gateway.fetch_grilla(7, _FECHA, fresca=True)

    assert runner.llamadas == [(7, _FECHA), (7, _FECHA)]


async def test_llamada_secundaria_reusa_la_ultima_grilla_cargada() -> None:
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]
    cargada = await gateway.fetch_grilla(7, _FECHA, fresca=True)

    reusada = await gateway.fetch_grilla(7, _FECHA)

    assert reusada is cargada
    assert len(runner.llamadas) == 1


async def test_llamada_secundaria_sin_grilla_previa_consulta() -> None:
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]

    await gateway.fetch_grilla(7, _FECHA)
    await gateway.fetch_grilla(8, _FECHA)

    assert runner.llamadas == [(7, _FECHA), (8, _FECHA)]


async def test_carga_fresca_reemplaza_la_grilla_que_reusan_las_secundarias() -> None:
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]
    await gateway.fetch_grilla(7, _FECHA, fresca=True)
    runner.filas = [_fila_cruda(c0=202)]
    await gateway.fetch_grilla(7, _FECHA, fresca=True)

    reusada = await gateway.fetch_grilla(7, _FECHA)

    assert [f.id_maquina for f in reusada] == [202]


async def test_la_recarga_de_otro_operador_no_cambia_la_grilla_reusada() -> None:
    # v1.7: cada operador trabaja sobre SU lista en memoria (`Index._equipos`).
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]
    await gateway.fetch_grilla(7, _FECHA, fresca=True, operador="ana")
    runner.filas = [_fila_cruda(c0=202)]
    await gateway.fetch_grilla(7, _FECHA, fresca=True, operador="beto")

    de_ana = await gateway.fetch_grilla(7, _FECHA, operador="ana")
    de_beto = await gateway.fetch_grilla(7, _FECHA, operador="beto")

    assert [f.id_maquina for f in de_ana] == [101]
    assert [f.id_maquina for f in de_beto] == [202]
    assert len(runner.llamadas) == 2


def test_timeout_de_la_grilla_es_el_del_legacy() -> None:
    # v1.7 `SiGesRepository.GetGrillaAsync`: `CommandTimeout = 180`.
    assert mod._TIMEOUT_SECONDS == 180.0


async def test_recuerda_un_numero_acotado_de_grillas(monkeypatch: Any) -> None:
    monkeypatch.setattr(mod, "_MAX_GRILLAS_RECORDADAS", 2)
    runner = FakeRunner([_fila_cruda()])
    gateway = PyodbcGrillaEstimacionGateway(runner)  # type: ignore[arg-type]
    for nro in (1, 2, 3):
        await gateway.fetch_grilla(nro, _FECHA, fresca=True)

    await gateway.fetch_grilla(1, _FECHA)  # la más vieja se descartó
    await gateway.fetch_grilla(3, _FECHA)  # sigue recordada

    assert [p[0] for p in runner.llamadas] == [1, 2, 3, 1]


async def test_velocidad_se_lee_como_entero_con_redondeo_bancario() -> None:
    # `ReadIntN` → `Convert.ToInt32(decimal)`: .5 va al par más cercano.
    assert (await _una_fila(c13=Decimal("45.5"))).velocidad == 46.0
    assert (await _una_fila(c13=Decimal("44.5"))).velocidad == 44.0
    assert (await _una_fila(c13=35)).velocidad == 35.0
    assert (await _una_fila(c13=None)).velocidad is None


async def test_prom_global_modelo_imp_de_la_columna_33() -> None:
    assert (await _una_fila(c33=Decimal("1234.50"))).prom_global_modelo_imp == 1234.5
    assert (await _una_fila()).prom_global_modelo_imp is None

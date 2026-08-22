"""PyodbcSigesCatalogoGateway: SQL que se envía y mapeo de filas pyodbc a los
DTOs del puerto. Sin conexión real: el MercurioQueryRunner se reemplaza por un
fake que registra llamadas y devuelve filas armadas a mano."""

from datetime import datetime
from types import SimpleNamespace
from typing import Any

from src.modules.liquidaciones.infrastructure.siges.pyodbc_siges_catalogo_gateway import (
    PyodbcSigesCatalogoGateway,
)
from src.modules.liquidaciones.infrastructure.siges.query import (
    CUADRICULAS_DE_PRESTADOR_SQL,
    SUCURSALES_DE_EMPRESA_SQL,
    SUCURSALES_DE_PRESTADOR_SQL,
    build_costos_habilitados_sql,
)


class FakeRunner:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows
        self.llamadas: list[tuple[str, Any, dict[str, Any]]] = []

    async def fetch_all(self, sql: str, params: Any = (), **kwargs: Any) -> list[Any]:
        self.llamadas.append((sql, params, kwargs))
        return self._rows


def _gateway(rows: list[Any]) -> tuple[PyodbcSigesCatalogoGateway, FakeRunner]:
    runner = FakeRunner(rows)
    return PyodbcSigesCatalogoGateway(runner), runner  # type: ignore[arg-type]


async def test_list_empresas_activas_clasifica_pst_y_spst() -> None:
    gateway, runner = _gateway(
        [
            SimpleNamespace(
                ID_Empresa=10, Den_Comercial=" PST Norte ", razon_social=" Norte SA ", cuit=None
            ),
            SimpleNamespace(
                ID_Empresa=11, Den_Comercial="SPST Sur", razon_social="  ", cuit="30-1"
            ),
        ]
    )
    empresas = await gateway.list_empresas_activas()

    assert [(e.siges_empresa_id, e.den_comercial, e.tipo) for e in empresas] == [
        (10, "PST Norte", "PST"),
        (11, "SPST Sur", "SPST"),
    ]
    assert empresas[0].razon_social == "Norte SA"
    assert empresas[0].cuit is None
    assert empresas[1].razon_social is None  # texto en blanco -> None
    assert runner.llamadas[0][2]["gateway"] == "siges_catalogo"


async def test_list_costos_habilitados_usa_placeholders_y_null_es_cero() -> None:
    gateway, runner = _gateway(
        [
            SimpleNamespace(
                ID_Empresa=10,
                descripcion=" Base ",
                fecha_vigencia=datetime(2026, 1, 15, 10, 30),
                CostoKm=None,
                correctivo="1500.50",
                preventivo=None,
                instalacion=2000,
                PreCorrectivo=None,
                guardia=0,
                sistemas=None,
            )
        ]
    )
    assert await gateway.list_costos_habilitados([]) == []
    assert runner.llamadas == []

    costos = await gateway.list_costos_habilitados([10, 11])

    sql, params, kwargs = runner.llamadas[0]
    assert sql == build_costos_habilitados_sql(2)
    assert "IN (?, ?)" in sql
    assert params == [10, 11]
    assert kwargs["log_extra"] == {"cantidad_ids": 2}
    costo = costos[0]
    assert costo.descripcion == "Base"
    assert costo.vigencia_desde.isoformat() == "2026-01-15"
    assert (costo.costo_km, costo.correctivo, costo.preventivo) == (0.0, 1500.5, 0.0)
    assert (costo.instalacion, costo.pre_correctivo, costo.guardia, costo.sistemas) == (
        2000.0, 0.0, 0.0, 0.0,
    )


async def test_list_sucursales_de_prestador_limpia_domicilio_de_plantilla() -> None:
    def fila(domicilio: Any, **extra: Any) -> SimpleNamespace:
        base: dict[str, Any] = dict(
            Id_Sucursal=501,
            Den_Comercial=" Cencosud ",
            descripcion=" Jumbo ",
            Domicilio=domicilio,
            DesCiudad=None,
            DesProvincia=" Buenos Aires ",
            Latitud=" -34.58 ",
            Longitud=None,
            Cuadricula="",
            IDCostoServicios="7",
        )
        base.update(extra)
        return SimpleNamespace(**base)

    gateway, runner = _gateway(
        [
            fila("Av. Santa Fe 4000 Piso: Dpto:"),
            fila(" 0 Piso: Dpto:", Id_Sucursal=502, IDCostoServicios=None),
            fila(None, Id_Sucursal=503),
        ]
    )
    sucursales = await gateway.list_sucursales_de_prestador(10)

    assert runner.llamadas[0][0] == SUCURSALES_DE_PRESTADOR_SQL
    assert runner.llamadas[0][1] == (10,)
    assert [s.domicilio for s in sucursales] == ["Av. Santa Fe 4000", None, None]
    primera = sucursales[0]
    assert (primera.siges_sucursal_id, primera.empresa_nombre, primera.sucursal_nombre) == (
        501, "Cencosud", "Jumbo",
    )
    assert (primera.localidad, primera.provincia) == (None, "Buenos Aires")
    assert (primera.latitud, primera.longitud, primera.cuadricula) == ("-34.58", None, None)
    assert primera.id_costo_servicios == 7
    assert sucursales[1].id_costo_servicios is None


async def test_list_cuadriculas_y_sucursales_propias() -> None:
    gateway, runner = _gateway(
        [SimpleNamespace(Cuadricula=" A1 "), SimpleNamespace(Cuadricula="B2")]
    )
    assert await gateway.list_cuadriculas_de_prestador(10) == ["A1", "B2"]
    assert runner.llamadas[0][0] == CUADRICULAS_DE_PRESTADOR_SQL
    assert runner.llamadas[0][1] == (10,)

    gateway, runner = _gateway(
        [
            SimpleNamespace(
                Id_Sucursal=900,
                descripcion=" Base Norte ",
                Latitud="-31.5",
                Longitud="-68.5",
                IDCostoServicios=3,
            )
        ]
    )
    propias = await gateway.list_sucursales_de_empresa(10)

    assert runner.llamadas[0][0] == SUCURSALES_DE_EMPRESA_SQL
    assert runner.llamadas[0][1] == (10,)
    assert (propias[0].siges_sucursal_id, propias[0].descripcion) == (900, "Base Norte")
    assert (propias[0].latitud, propias[0].longitud) == ("-31.5", "-68.5")
    assert propias[0].id_costo_servicios == 3

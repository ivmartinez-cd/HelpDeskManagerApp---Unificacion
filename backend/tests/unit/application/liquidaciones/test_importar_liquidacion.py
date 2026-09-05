"""Tests de ImportarLiquidacion — orquestación (validar prestador, parsear archivo,
crear liquidación + incidentes, delegar análisis en ReanalizarLiquidacion).
La lógica del parser y del motor de reglas ya están cubiertas por sus propios tests;
acá solo se verifica que el caso de uso conecta las piezas correctamente."""

import uuid
from datetime import date

import pytest

from src.modules.liquidaciones.application.use_cases.importar_liquidacion import (
    ImportarLiquidacion,
    ImportarLiquidacionPorts,
)
from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.domain.errors import PrestadorNoEncontradoError
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
    ResultadoImportacion,
)
from tests.unit.domain.liquidaciones.factories import (
    make_prestador,
    make_tarifario,
    reglas_activas_default,
)
from tests.unit.domain.liquidaciones.fakes import (
    FakeLiquidacionFileParser,
    FakePrestadorRepository,
    FakeReglaAlertaRepository,
    FakeTablaKmRepository,
    FakeTarifarioRepository,
)
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
    FakeLiquidacionRepository,
)

ARCHIVO_NOMBRE = "liquidacion_TEST_2026-01.xls"
ARCHIVO_CONTENIDO = b"<contenido-fake>"


def make_resultado_parseo(
    incidentes: list[IncidenteImportado] | None = None,
    *,
    numero_liquidacion: str = "1-1",
    periodo: str = "2026-01",
    tipo_liquidacion: str = "regular",
) -> ResultadoImportacion:
    return ResultadoImportacion(
        numero_liquidacion=numero_liquidacion,
        periodo=periodo,
        tipo_liquidacion=tipo_liquidacion,
        incidentes=incidentes or [],
    )


def make_incidente_importado(**overrides: object) -> IncidenteImportado:
    defaults: dict[str, object] = {
        "numero_incidente": "INC-001",
        "rubro": None,
        "tipo": "correctivo",
        "empresa_nombre": "Empresa Test",
        "sucursal_nombre": "Sucursal Test",
        "nro_serie": None,
        "fecha_cierre": date(2026, 1, 15),
        "costo_servicio_cobrado": 1500.0,
        "cant_km_cobrado": 0.0,
        "costo_km_cobrado": 0.0,
        "total_viaje_cobrado": 0.0,
        "costo_total_cobrado": 1500.0,
        "pasa_it": True,
    }
    defaults.update(overrides)
    return IncidenteImportado(**defaults)  # type: ignore[arg-type]


class World:
    def __init__(
        self,
        resultado_parseo: ResultadoImportacion | None = None,
    ) -> None:
        self.prestadores = FakePrestadorRepository()
        self.liquidaciones = FakeLiquidacionRepository()
        self.incidentes = FakeIncidenteRepository()
        self.alertas = FakeAlertaRepository()
        self.reglas = FakeReglaAlertaRepository(reglas_activas_default())
        self.tablas_km = FakeTablaKmRepository()
        self.tarifarios = FakeTarifarioRepository()
        self.parser = FakeLiquidacionFileParser(
            resultado_parseo or make_resultado_parseo()
        )

        reanalizar = ReanalizarLiquidacion(
            ReanalizarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                alertas=self.alertas,
                reglas=self.reglas,
                tablas_km=self.tablas_km,
                tarifarios=self.tarifarios,
            )
        )
        self.use_case = ImportarLiquidacion(
            ImportarLiquidacionPorts(
                parser=self.parser,
                prestadores=self.prestadores,
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                reanalizar=reanalizar,
            )
        )


async def test_prestador_inexistente_lanza_error() -> None:
    world = World()

    with pytest.raises(PrestadorNoEncontradoError):
        await world.use_case.execute(
            prestador_id=uuid.uuid4(),
            contenido=ARCHIVO_CONTENIDO,
            nombre_archivo=ARCHIVO_NOMBRE,
        )


async def test_happy_path_crea_liquidacion_con_totales_del_parseo() -> None:
    """El caso de uso persiste la liquidación con `total_incidentes` y `total_importe`
    derivados de lo que devuelve el parser — sin un segundo UPDATE a la DB."""
    incidente_a = make_incidente_importado(costo_total_cobrado=1500.0)
    incidente_b = make_incidente_importado(
        numero_incidente="INC-002", costo_total_cobrado=2000.0
    )
    resultado_parseo = make_resultado_parseo(incidentes=[incidente_a, incidente_b])
    prestador = make_prestador()

    world = World(resultado_parseo=resultado_parseo)
    world.prestadores.rows[prestador.id] = prestador

    resultado = await world.use_case.execute(
        prestador_id=prestador.id,
        contenido=ARCHIVO_CONTENIDO,
        nombre_archivo=ARCHIVO_NOMBRE,
    )

    assert resultado.total_incidentes == 2
    liquidaciones = list(world.liquidaciones.rows.values())
    assert len(liquidaciones) == 1
    liq = liquidaciones[0]
    assert liq.total_incidentes == 2
    assert liq.total_importe == pytest.approx(3500.0)
    assert liq.prestador_id == prestador.id
    assert liq.numero_liquidacion == "1-1"
    assert liq.periodo == "2026-01"
    assert liq.nombre_archivo == ARCHIVO_NOMBRE


async def test_happy_path_crea_incidentes_via_bulk_create() -> None:
    incidente = make_incidente_importado()
    resultado_parseo = make_resultado_parseo(incidentes=[incidente])
    prestador = make_prestador()

    world = World(resultado_parseo=resultado_parseo)
    world.prestadores.rows[prestador.id] = prestador

    await world.use_case.execute(
        prestador_id=prestador.id,
        contenido=ARCHIVO_CONTENIDO,
        nombre_archivo=ARCHIVO_NOMBRE,
    )

    assert len(world.incidentes.rows) == 1
    creado = next(iter(world.incidentes.rows.values()))
    assert creado.numero_incidente == incidente.numero_incidente
    assert creado.costo_total_cobrado == incidente.costo_total_cobrado


async def test_happy_path_dispara_reanalizar_y_retorna_sus_totales() -> None:
    """El resultado del caso de uso proviene de `ReanalizarLiquidacion`, no de un
    conteo propio — si el motor genera alertas, el DTO las refleja."""
    prestador = make_prestador()
    incidente = make_incidente_importado(costo_servicio_cobrado=1800.0)
    resultado_parseo = make_resultado_parseo(incidentes=[incidente])

    world = World(resultado_parseo=resultado_parseo)
    world.prestadores.rows[prestador.id] = prestador
    world.tarifarios.rows = [
        make_tarifario(prestador_id=prestador.id, costo_servicio=1500.0)
    ]

    resultado = await world.use_case.execute(
        prestador_id=prestador.id,
        contenido=ARCHIVO_CONTENIDO,
        nombre_archivo=ARCHIVO_NOMBRE,
    )

    assert resultado.total_incidentes == 1
    assert resultado.total_alertas == 1  # ALT001: precio cobrado > tarifario
    assert resultado.liquidacion_id in world.liquidaciones.rows


async def test_parser_recibe_contenido_y_nombre_de_archivo() -> None:
    prestador = make_prestador()
    world = World()
    world.prestadores.rows[prestador.id] = prestador

    await world.use_case.execute(
        prestador_id=prestador.id,
        contenido=ARCHIVO_CONTENIDO,
        nombre_archivo=ARCHIVO_NOMBRE,
    )

    assert len(world.parser.calls) == 1
    contenido_recibido, nombre_recibido = world.parser.calls[0]
    assert contenido_recibido == ARCHIVO_CONTENIDO
    assert nombre_recibido == ARCHIVO_NOMBRE

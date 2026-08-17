"""Tests de ReanalizarLiquidacion — orquestación (carga de datos, corrida del motor,
persistencia). La lógica de negocio del motor en sí ya está cubierta por los 22 tests
de `tests/unit/domain/liquidaciones/test_motor_reglas.py`; acá solo se verifica que el
caso de uso conecta las piezas correctamente."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.reanalizar_liquidacion import (
    ReanalizarLiquidacion,
    ReanalizarLiquidacionPorts,
)
from src.modules.liquidaciones.domain.errors import LiquidacionNoEncontradaError
from tests.unit.domain.liquidaciones.factories import (
    make_incidente,
    make_liquidacion,
    make_tarifario,
    reglas_activas_default,
)
from tests.unit.domain.liquidaciones.fakes import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
    FakeLiquidacionRepository,
    FakeObservacionRepository,
    FakeReglaAlertaRepository,
    FakeSpstRepository,
    FakeTablaKmRepository,
    FakeTarifarioRepository,
)


class World:
    def __init__(self) -> None:
        self.liquidaciones = FakeLiquidacionRepository()
        self.incidentes = FakeIncidenteRepository()
        self.alertas = FakeAlertaRepository()
        self.observaciones = FakeObservacionRepository()
        self.reglas = FakeReglaAlertaRepository(reglas_activas_default())
        self.tablas_km = FakeTablaKmRepository()
        self.spsts = FakeSpstRepository()
        self.tarifarios = FakeTarifarioRepository()
        self.use_case = ReanalizarLiquidacion(
            ReanalizarLiquidacionPorts(
                liquidaciones=self.liquidaciones,
                incidentes=self.incidentes,
                alertas=self.alertas,
                observaciones=self.observaciones,
                reglas=self.reglas,
                tablas_km=self.tablas_km,
                spsts=self.spsts,
                tarifarios=self.tarifarios,
            )
        )


async def test_liquidacion_no_encontrada_lanza_error() -> None:
    world = World()

    with pytest.raises(LiquidacionNoEncontradaError):
        await world.use_case.execute(uuid.uuid4())


async def test_reanalizar_corre_el_motor_y_persiste_alertas() -> None:
    world = World()
    prestador_id = uuid.uuid4()
    liquidacion = make_liquidacion(prestador_id=prestador_id, total_alertas=0)
    world.liquidaciones.rows[liquidacion.id] = liquidacion

    tarifario = make_tarifario(prestador_id=prestador_id, costo_servicio=1500.0)
    world.tarifarios.rows = [tarifario]

    incidente = make_incidente(liquidacion_id=liquidacion.id, costo_servicio_cobrado=1800.0)
    world.incidentes.rows[incidente.id] = incidente

    resultado = await world.use_case.execute(liquidacion.id)

    assert resultado.total_incidentes == 1
    assert resultado.total_alertas == 1
    assert resultado.total_observaciones == 0

    alertas_creadas = world.alertas.por_liquidacion[liquidacion.id]
    assert len(alertas_creadas) == 1
    assert alertas_creadas[0].tipo_alerta == "ALT001"

    incidente_actualizado = world.incidentes.rows[incidente.id]
    assert incidente_actualizado.costo_servicio_esperado == 1500.0
    assert incidente_actualizado.estado_validacion == "con_alertas"

    assert world.liquidaciones.rows[liquidacion.id].total_alertas == 1


async def test_reanalizar_reemplaza_en_vez_de_acumular() -> None:
    """Correr el caso de uso dos veces sobre la misma liquidación no duplica alertas
    — mismo comportamiento idempotente que `ejecutar_motor` del legacy."""
    world = World()
    prestador_id = uuid.uuid4()
    liquidacion = make_liquidacion(prestador_id=prestador_id)
    world.liquidaciones.rows[liquidacion.id] = liquidacion
    world.tarifarios.rows = [make_tarifario(prestador_id=prestador_id, costo_servicio=1500.0)]
    incidente = make_incidente(liquidacion_id=liquidacion.id, costo_servicio_cobrado=1800.0)
    world.incidentes.rows[incidente.id] = incidente

    await world.use_case.execute(liquidacion.id)
    resultado_2 = await world.use_case.execute(liquidacion.id)

    assert resultado_2.total_alertas == 1
    assert len(world.alertas.por_liquidacion[liquidacion.id]) == 1


async def test_reanalizar_preserva_el_triage_de_la_tl() -> None:
    """EL test de la gestión de alertas: la TL descarta una alerta con
    justificación, se re-analiza, y la alerta regenerada conserva estado y
    justificación (clave (incidente_id, tipo_alerta) — ver conciliar_alertas)."""
    world = World()
    prestador_id = uuid.uuid4()
    liquidacion = make_liquidacion(prestador_id=prestador_id)
    world.liquidaciones.rows[liquidacion.id] = liquidacion
    world.tarifarios.rows = [make_tarifario(prestador_id=prestador_id, costo_servicio=1500.0)]
    incidente = make_incidente(liquidacion_id=liquidacion.id, costo_servicio_cobrado=1800.0)
    world.incidentes.rows[incidente.id] = incidente

    await world.use_case.execute(liquidacion.id)
    alerta = world.alertas.por_liquidacion[liquidacion.id][0]
    await world.alertas.update_estado(
        liquidacion.id, alerta.id,
        estado="descartada", justificacion="Diferencia acordada con el PST",
    )

    await world.use_case.execute(liquidacion.id)

    regenerada = world.alertas.por_liquidacion[liquidacion.id][0]
    assert regenerada.id != alerta.id  # es una fila nueva del reemplazo
    assert regenerada.estado == "descartada"
    assert regenerada.justificacion == "Diferencia acordada con el PST"


async def test_reanalizar_regenera_pendientes_sin_arrastre() -> None:
    """Una alerta que la TL NO trabajó (pendiente) se regenera limpia."""
    world = World()
    prestador_id = uuid.uuid4()
    liquidacion = make_liquidacion(prestador_id=prestador_id)
    world.liquidaciones.rows[liquidacion.id] = liquidacion
    world.tarifarios.rows = [make_tarifario(prestador_id=prestador_id, costo_servicio=1500.0)]
    incidente = make_incidente(liquidacion_id=liquidacion.id, costo_servicio_cobrado=1800.0)
    world.incidentes.rows[incidente.id] = incidente

    await world.use_case.execute(liquidacion.id)
    await world.use_case.execute(liquidacion.id)

    regenerada = world.alertas.por_liquidacion[liquidacion.id][0]
    assert regenerada.estado == "pendiente"
    assert regenerada.justificacion is None

"""Tests de ActualizarEstadoAlerta — además de cambiar el estado de la alerta,
recalcula `estado_validacion` del incidente dueño (ver `recalcular_estado_incidente`)."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.actualizar_estado_alerta import (
    ActualizarEstadoAlerta,
    ActualizarEstadoAlertaPorts,
)
from src.modules.liquidaciones.domain.errors import IncidenteRelacionadoInvalidoError
from tests.unit.domain.liquidaciones.factories import make_alerta, make_incidente
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
)


class World:
    def __init__(self) -> None:
        self.alertas = FakeAlertaRepository()
        self.incidentes = FakeIncidenteRepository()
        self.use_case = ActualizarEstadoAlerta(
            ActualizarEstadoAlertaPorts(alertas=self.alertas, incidentes=self.incidentes)
        )


async def test_alerta_inexistente_devuelve_none() -> None:
    world = World()

    resultado = await world.use_case.execute(
        uuid.uuid4(), uuid.uuid4(), estado="resuelta", justificacion=None
    )

    assert resultado is None


async def test_unica_alerta_resuelta_deja_incidente_ok() -> None:
    world = World()
    liq_id, inc_id = uuid.uuid4(), uuid.uuid4()
    incidente = make_incidente(id=inc_id, liquidacion_id=liq_id, estado_validacion="con_alertas")
    world.incidentes.rows[inc_id] = incidente
    alerta = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="pendiente")
    world.alertas.por_liquidacion[liq_id] = [alerta]

    actualizada = await world.use_case.execute(
        liq_id, alerta.id, estado="resuelta", justificacion=None
    )

    assert actualizada is not None
    assert actualizada.estado == "resuelta"
    assert world.incidentes.rows[inc_id].estado_validacion == "ok"


async def test_descartar_una_de_dos_alertas_mantiene_con_alertas() -> None:
    world = World()
    liq_id, inc_id = uuid.uuid4(), uuid.uuid4()
    world.incidentes.rows[inc_id] = make_incidente(
        id=inc_id, liquidacion_id=liq_id, estado_validacion="con_alertas"
    )
    a1 = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="pendiente")
    a2 = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="pendiente")
    world.alertas.por_liquidacion[liq_id] = [a1, a2]

    await world.use_case.execute(
        liq_id, a1.id, estado="descartada", justificacion="no aplica"
    )

    assert world.incidentes.rows[inc_id].estado_validacion == "con_alertas"


async def test_reabrir_alerta_resuelta_vuelve_incidente_a_con_alertas() -> None:
    world = World()
    liq_id, inc_id = uuid.uuid4(), uuid.uuid4()
    world.incidentes.rows[inc_id] = make_incidente(
        id=inc_id, liquidacion_id=liq_id, estado_validacion="ok"
    )
    alerta = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="resuelta")
    world.alertas.por_liquidacion[liq_id] = [alerta]

    await world.use_case.execute(liq_id, alerta.id, estado="en_revision", justificacion=None)

    assert world.incidentes.rows[inc_id].estado_validacion == "con_alertas"


async def test_vincular_incidente_de_otra_liquidacion_falla() -> None:
    world = World()
    liq_id, inc_id = uuid.uuid4(), uuid.uuid4()
    otra_liq_id, otro_inc_id = uuid.uuid4(), uuid.uuid4()
    world.incidentes.rows[inc_id] = make_incidente(
        id=inc_id, liquidacion_id=liq_id, estado_validacion="con_alertas"
    )
    world.incidentes.rows[otro_inc_id] = make_incidente(
        id=otro_inc_id, liquidacion_id=otra_liq_id, estado_validacion="ok"
    )
    alerta = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="pendiente")
    world.alertas.por_liquidacion[liq_id] = [alerta]

    with pytest.raises(IncidenteRelacionadoInvalidoError):
        await world.use_case.execute(
            liq_id,
            alerta.id,
            estado="descartada",
            justificacion="se suma al recorrido del otro caso",
            incidente_relacionado_id=otro_inc_id,
        )


async def test_vincular_incidente_de_la_misma_liquidacion_persiste() -> None:
    world = World()
    liq_id, inc_id, inc_relacionado_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    world.incidentes.rows[inc_id] = make_incidente(
        id=inc_id, liquidacion_id=liq_id, estado_validacion="con_alertas"
    )
    world.incidentes.rows[inc_relacionado_id] = make_incidente(
        id=inc_relacionado_id, liquidacion_id=liq_id, estado_validacion="ok"
    )
    alerta = make_alerta(liquidacion_id=liq_id, incidente_id=inc_id, estado="pendiente")
    world.alertas.por_liquidacion[liq_id] = [alerta]

    actualizada = await world.use_case.execute(
        liq_id,
        alerta.id,
        estado="descartada",
        justificacion="se suma al recorrido del otro caso",
        incidente_relacionado_id=inc_relacionado_id,
    )

    assert actualizada is not None
    assert actualizada.incidente_relacionado_id == inc_relacionado_id

"""Tests de ActualizarEstadoAlertasLote — varias alertas con el mismo estado y
motivo; valida el lote entero antes de tocar nada, preserva el vínculo de ruta
compartida y recalcula `estado_validacion` de cada incidente afectado."""

import uuid

import pytest

from src.modules.liquidaciones.application.use_cases.actualizar_estado_alerta import (
    ActualizarEstadoAlertaPorts,
)
from src.modules.liquidaciones.application.use_cases.actualizar_estado_alertas_lote import (
    ActualizarEstadoAlertasLote,
)
from src.modules.liquidaciones.domain.errors import AlertasNoEncontradasError
from tests.unit.domain.liquidaciones.factories import make_alerta, make_incidente
from tests.unit.domain.liquidaciones.fakes_liquidacion import (
    FakeAlertaRepository,
    FakeIncidenteRepository,
)


class World:
    def __init__(self) -> None:
        self.alertas = FakeAlertaRepository()
        self.incidentes = FakeIncidenteRepository()
        self.use_case = ActualizarEstadoAlertasLote(
            ActualizarEstadoAlertaPorts(alertas=self.alertas, incidentes=self.incidentes)
        )
        self.liq_id = uuid.uuid4()

    def incidente_con_alertas(self, *estados: str) -> tuple[uuid.UUID, list]:
        inc_id = uuid.uuid4()
        self.incidentes.rows[inc_id] = make_incidente(
            id=inc_id, liquidacion_id=self.liq_id, estado_validacion="con_alertas"
        )
        alertas = [
            make_alerta(liquidacion_id=self.liq_id, incidente_id=inc_id, estado=e) for e in estados
        ]
        self.alertas.por_liquidacion.setdefault(self.liq_id, []).extend(alertas)
        return inc_id, alertas


async def test_resuelve_varias_alertas_de_distintos_incidentes_con_el_mismo_motivo() -> None:
    world = World()
    inc_a, [a1] = world.incidente_con_alertas("pendiente")
    inc_b, [b1] = world.incidente_con_alertas("en_revision")

    actualizadas = await world.use_case.execute(
        world.liq_id, [a1.id, b1.id], estado="resuelta", justificacion="costo doble acordado"
    )

    assert [a.estado for a in actualizadas] == ["resuelta", "resuelta"]
    assert all(a.justificacion == "costo doble acordado" for a in actualizadas)
    assert world.incidentes.rows[inc_a].estado_validacion == "ok"
    assert world.incidentes.rows[inc_b].estado_validacion == "ok"


async def test_incidente_con_otra_alerta_abierta_sigue_con_alertas() -> None:
    world = World()
    inc_id, [a1, _a2] = world.incidente_con_alertas("pendiente", "pendiente")

    await world.use_case.execute(
        world.liq_id, [a1.id], estado="descartada", justificacion="no aplica"
    )

    assert world.incidentes.rows[inc_id].estado_validacion == "con_alertas"


async def test_alerta_ajena_rechaza_el_lote_entero_sin_cambiar_nada() -> None:
    world = World()
    inc_id, [a1] = world.incidente_con_alertas("pendiente")
    ajena = uuid.uuid4()

    with pytest.raises(AlertasNoEncontradasError):
        await world.use_case.execute(
            world.liq_id, [a1.id, ajena], estado="resuelta", justificacion=None
        )

    assert world.alertas.por_liquidacion[world.liq_id][0].estado == "pendiente"
    assert world.incidentes.rows[inc_id].estado_validacion == "con_alertas"


async def test_preserva_el_vinculo_de_ruta_compartida() -> None:
    world = World()
    inc_id, _ = world.incidente_con_alertas()
    relacionado = uuid.uuid4()
    alerta = make_alerta(
        liquidacion_id=world.liq_id,
        incidente_id=inc_id,
        estado="pendiente",
        incidente_relacionado_id=relacionado,
    )
    world.alertas.por_liquidacion[world.liq_id].append(alerta)

    [actualizada] = await world.use_case.execute(
        world.liq_id, [alerta.id], estado="resuelta", justificacion=None
    )

    assert actualizada.incidente_relacionado_id == relacionado


async def test_ids_repetidos_se_aplican_una_sola_vez() -> None:
    world = World()
    _, [a1] = world.incidente_con_alertas("pendiente")

    actualizadas = await world.use_case.execute(
        world.liq_id, [a1.id, a1.id], estado="en_revision", justificacion=None
    )

    assert len(actualizadas) == 1

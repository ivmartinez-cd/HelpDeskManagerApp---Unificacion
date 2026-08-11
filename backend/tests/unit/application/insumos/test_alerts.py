"""Tests de ListAlerts / AcknowledgeAlerts — GET y POST /api/insumos/alerts."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from src.modules.insumos.application.use_cases.list_alerts import (
    AcknowledgeAlerts,
    AlertsPorts,
    ListAlerts,
)
from src.modules.insumos.domain.entities.request_alert import (
    STATE_ACKNOWLEDGED,
    STATE_ESCALATED,
    STATE_TRIGGERED,
)
from tests.unit.domain.insumos.fakes import (
    FakeInsumosSettingsRepository,
    FakeRequestAlertRepository,
)

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
HACE_MUCHO = datetime.now(UTC) - timedelta(days=2)
RECIEN = datetime.now(UTC)


class World:
    def __init__(self) -> None:
        self.alerts = FakeRequestAlertRepository()
        self.settings = FakeInsumosSettingsRepository()
        # Horario laboral desactivado por default: los tests que miden la ventana en
        # sí viven en el dominio, acá no puede depender del día en que corra la suite.
        self.settings.raw = {"alert_work_hours_enabled": "0"}
        ports = AlertsPorts(
            alerts=self.alerts,  # type: ignore[arg-type]
            settings=self.settings,  # type: ignore[arg-type]
        )
        self.list = ListAlerts(ports, TZ)
        self.ack = AcknowledgeAlerts(ports)


async def test_una_alerta_vencida_escala_al_consultar_sin_esperar_al_job() -> None:
    """El GET es lo que pollea el frontend: escalar ahí deja la escalada precisa al
    minuto sin depender del job de fondo (que ni siquiera está portado)."""
    world = World()
    world.alerts.add(1, STATE_TRIGGERED, requested_at=HACE_MUCHO)

    alerts = await world.list.execute()

    assert [a.hp_request_id for a in alerts] == [1]
    assert world.alerts.states[1] == STATE_ESCALATED


async def test_una_alerta_que_todavia_no_vencio_no_escala() -> None:
    world = World()
    world.alerts.add(1, STATE_TRIGGERED, requested_at=RECIEN)

    alerts = await world.list.execute()

    assert alerts == []
    assert world.alerts.states[1] == STATE_TRIGGERED


async def test_una_alerta_sin_fecha_de_solicitud_nunca_escala() -> None:
    """Sin `requested_at` no se sabe hace cuánto espera el cliente: no se inventa."""
    world = World()
    world.alerts.add(1, STATE_TRIGGERED, requested_at=None)

    assert await world.list.execute() == []


async def test_fuera_del_horario_laboral_no_se_escala_pero_se_siguen_viendo() -> None:
    world = World()
    world.settings.raw = {
        "alert_work_hours_enabled": "1",
        "alert_work_hour_start": "8",
        "alert_work_hour_end": "8",  # ventana vacía: nunca es horario laboral
    }
    world.alerts.add(1, STATE_TRIGGERED, requested_at=HACE_MUCHO)
    world.alerts.add(2, STATE_ESCALATED, requested_at=HACE_MUCHO)

    alerts = await world.list.execute()

    assert world.alerts.escalate_calls == []  # ni se intentó escalar
    assert [a.hp_request_id for a in alerts] == [2]  # lo ya escalado sigue visible


async def test_las_reconocidas_dejan_de_ser_activas() -> None:
    world = World()
    world.alerts.add(1, STATE_ESCALATED, requested_at=HACE_MUCHO)

    assert await world.ack.execute([1]) == 1
    assert world.alerts.states[1] == STATE_ACKNOWLEDGED
    assert await world.list.execute() == []


async def test_solo_se_reconoce_lo_que_ya_escalo() -> None:
    """Reconocer algo que todavía no venció no significa nada."""
    world = World()
    world.alerts.add(1, STATE_TRIGGERED, requested_at=RECIEN)

    assert await world.ack.execute([1]) == 0
    assert world.alerts.states[1] == STATE_TRIGGERED


async def test_reconocer_una_lista_vacia_no_hace_nada() -> None:
    world = World()

    assert await world.ack.execute([]) == 0


async def test_el_umbral_de_escalado_sale_de_la_configuracion() -> None:
    world = World()
    world.settings.raw["alert_escalation_minutes"] = "30"
    world.alerts.add(1, STATE_TRIGGERED, requested_at=datetime.now(UTC) - timedelta(minutes=45))

    alerts = await world.list.execute()

    assert [a.hp_request_id for a in alerts] == [1]

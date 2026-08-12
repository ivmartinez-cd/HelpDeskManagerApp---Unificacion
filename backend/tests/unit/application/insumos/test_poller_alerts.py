"""Tests de PollerAlerts — una sola alerta por caída, una sola recuperación por vuelta."""

import pytest

from src.modules.insumos.application.jobs.poller_alerts import PollerAlerts
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    KIND_POLLER_ALERT,
    KIND_POLLER_RECOVERY,
)
from tests.unit.domain.insumos.fakes import FakeMailDispatcher


async def test_por_debajo_del_umbral_no_despacha_nada() -> None:
    dispatcher = FakeMailDispatcher()
    alerts = PollerAlerts(dispatcher, threshold=3)

    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")

    assert dispatcher.dispatched == []


async def test_al_llegar_al_umbral_despacha_una_sola_vez_con_kind_poller_alert() -> None:
    dispatcher = FakeMailDispatcher()
    alerts = PollerAlerts(dispatcher, threshold=2)

    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")

    assert len(dispatcher.dispatched) == 1
    assert dispatcher.dispatched[0].kind == KIND_POLLER_ALERT


async def test_mientras_sigue_caido_no_vuelve_a_despachar() -> None:
    dispatcher = FakeMailDispatcher()
    alerts = PollerAlerts(dispatcher, threshold=2)

    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")

    assert len(dispatcher.dispatched) == 1


async def test_en_la_recuperacion_despacha_poller_recovery_y_resetea_el_contador() -> None:
    dispatcher = FakeMailDispatcher()
    alerts = PollerAlerts(dispatcher, threshold=2)
    await alerts.record_failure("timeout")
    await alerts.record_failure("timeout")

    await alerts.record_success()

    assert len(dispatcher.dispatched) == 2
    assert dispatcher.dispatched[1].kind == KIND_POLLER_RECOVERY
    # El contador se reinició: hacen falta otras `threshold` caídas para alertar de nuevo.
    await alerts.record_failure("timeout")
    assert len(dispatcher.dispatched) == 2


async def test_sin_caida_previa_record_success_no_despacha_nada() -> None:
    dispatcher = FakeMailDispatcher()
    alerts = PollerAlerts(dispatcher, threshold=2)

    await alerts.record_success()

    assert dispatcher.dispatched == []


async def test_dispatcher_que_revienta_no_tumba_la_suite_de_tests() -> None:
    """PollerAlerts confía por completo en el contrato de MailDispatcher.dispatch
    ("nunca propaga") y no agrega su propia red de contención — se invoca sin try/except
    desde `_run_sync_cycle`. Este fake rompe el contrato a propósito para dejar documentado
    qué pasaría si una implementación real lo violara: la excepción sí llega hasta el
    caller. El `pytest.raises` es lo que evita que la excepción tumbe la corrida del test."""
    dispatcher = FakeMailDispatcher()
    dispatcher.should_raise = True
    alerts = PollerAlerts(dispatcher, threshold=1)

    with pytest.raises(RuntimeError):
        await alerts.record_failure("timeout")

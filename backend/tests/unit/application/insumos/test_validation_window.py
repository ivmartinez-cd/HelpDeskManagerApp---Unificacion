"""Tests de ValidationWindow — port de la parte de start/resolve de
test_request_validation.py del legacy (la semántica del UPSERT en sí se prueba en
integración contra Postgres).

Caso real que motivó la feature: equipo MXBCQ7C03T (ago-2026) — Insight reportó un
cartucho en 0% por un glitch de lectura del sensor, la app autocargó un pedido 23
minutos después, y el nivel real (87%) ya estaba disponible desde antes."""

from src.modules.insumos.application.use_cases.validation_window import (
    ValidationWindow,
    ValidationWindowPorts,
)
from src.modules.insumos.domain.entities.audit_record import EVENT_AUTO_DISMISSED
from src.modules.insumos.domain.services.validation_diagnosis import ValidationDiagnosis
from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_CONFIRMED,
    VALIDATION_DISMISSED,
    PendingValidationWork,
)
from tests.unit.domain.insumos.fakes import (
    FakeInsightGateway,
    FakeOrderAuditRepository,
    FakeRequestValidationRepository,
    FakeWsAycGateway,
)

REQUEST = {
    "id": 974730,
    "deviceId": 203709,
    "customerId": 1,
    "requested": "2026-08-04T11:30:05.000Z",
    "consumable": {
        "sku": "W9008MC",
        "description": "Cartucho negro HP W9008MC",
        "percentLeft": 0,
        "daysLeft": 0,
        "pagesLeft": 0,
        "index": 1,
        "serialNumber": "",
    },
}


class World:
    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.validations = FakeRequestValidationRepository()
        self.audit = FakeOrderAuditRepository()
        self.window = ValidationWindow(
            ValidationWindowPorts(
                insight=self.insight,  # type: ignore[arg-type]
                validations=self.validations,
                audit=self.audit,
                diagnosis=ValidationDiagnosis(self.insight, FakeWsAycGateway()),  # type: ignore[arg-type]
            )
        )

    async def start(self, deadline_minutes: int) -> None:
        await self.window.start_pending(
            REQUEST,
            device_id=203709,
            customer_id=1,
            device_serial="MXBCQ7C03T",
            deadline_minutes=deadline_minutes,
        )


async def test_recuperacion_temprana_no_espera_el_techo_y_se_elimina_en_sds() -> None:
    """El nivel en vivo se recuperó -> DISMISSED al toque aunque falte ventana, con
    evento AUTO_DISMISSED en el Historial y baja en HP SDS (status_update=DELETE, el
    mismo que el Descartar manual) con el detalle como comentario."""
    world = World()
    await world.start(deadline_minutes=360)  # 6hs — ni cerca de vencer
    world.insight.consumables_by_device[203709] = [{"sku": "W9008MC", "percentLeft": 87}]

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.resolved == [(974730, VALIDATION_DISMISSED)]
    assert len(world.audit.records) == 1
    record = world.audit.records[0]
    assert record.event == EVENT_AUTO_DISMISSED
    assert record.hp_request_id == 974730
    assert record.device_serial == "MXBCQ7C03T"
    assert record.detail is not None and "87%" in record.detail
    assert len(world.insight.updates) == 1
    call = world.insight.updates[0]
    assert call["request_id"] == 974730
    assert call["statusUpdate"] == "DELETE"
    assert "87%" in call["comment"]


async def test_si_falla_la_baja_en_sds_el_descarte_local_queda_firme_igual() -> None:
    """Best-effort: si el DELETE en Insight falla, el DISMISSED local queda igual
    (nunca se vuelve a autocargar) y el Historial lo señala para revisión manual."""
    world = World()
    await world.start(deadline_minutes=0)
    world.insight.consumables_by_device[203709] = [{"sku": "W9008MC", "percentLeft": 87}]
    world.insight.update_error = RuntimeError("Insight caído")

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.statuses[974730] == VALIDATION_DISMISSED
    record = world.audit.records[0]
    assert record.event == EVENT_AUTO_DISMISSED
    assert record.detail is not None
    assert "no se pudo eliminar la solicitud en HP SDS" in record.detail


async def test_nivel_sigue_bajo_y_vencio_el_techo_se_confirma() -> None:
    world = World()
    await world.start(deadline_minutes=0)  # deadline_minutes=0 => ya venció
    world.insight.consumables_by_device[203709] = [{"sku": "W9008MC", "percentLeft": 3}]

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.resolved == [(974730, VALIDATION_CONFIRMED)]
    assert world.audit.records == []  # CONFIRMED no genera evento propio
    assert world.insight.updates == []


async def test_nivel_sigue_bajo_pero_no_vencio_sigue_pending() -> None:
    world = World()
    await world.start(deadline_minutes=360)
    world.insight.consumables_by_device[203709] = [{"sku": "W9008MC", "percentLeft": 3}]

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.resolved == []
    assert 974730 in world.validations.pending


async def test_fail_closed_si_no_puede_consultar_el_equipo() -> None:
    world = World()
    await world.start(deadline_minutes=0)
    world.insight.consumables_error = RuntimeError("Insight caído")

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.resolved == []
    assert 974730 in world.validations.pending


async def test_fail_closed_si_el_sku_ya_no_aparece() -> None:
    """Reemplazo real, equipo dado de baja, etc. — mejor no resolver que resolver mal."""
    world = World()
    await world.start(deadline_minutes=0)
    world.insight.consumables_by_device[203709] = [{"sku": "OTRO-SKU", "percentLeft": 50}]

    await world.window.resolve_pending(min_percent=15)

    assert world.validations.resolved == []
    assert 974730 in world.validations.pending


async def test_start_no_reconsulta_insight_si_ya_se_diagnostico() -> None:
    """Ver la misma solicitud dos veces (dos vistas del dashboard) no recalcula el
    diagnóstico ni vuelve a tocar la fila — swap_checked es el gate único."""
    world = World()
    await world.start(deadline_minutes=60)
    assert len(world.validations.starts) == 1

    await world.start(deadline_minutes=60)

    assert len(world.validations.starts) == 1  # no hubo segundo start


async def test_carrera_perdida_no_duplica_el_evento_en_el_historial() -> None:
    """Si otro proceso resolvió la fila entre get_all_pending y resolve, esta llamada
    no registra AUTO_DISMISSED ni manda el DELETE a HP SDS."""
    world = World()
    world.insight.consumables_by_device[203709] = [{"sku": "W9008MC", "percentLeft": 87}]
    # Estado de carrera: la fila salió en el barrido pero ya no está PENDING.
    world.validations.work[974730] = PendingValidationWork(
        hp_request_id=974730,
        customer_id=1,
        device_id=203709,
        device_serial="MXBCQ7C03T",
        sku="W9008MC",
        initial_percent_left=0.0,
        is_due=False,
    )
    world.validations.statuses[974730] = VALIDATION_DISMISSED

    await world.window.resolve_pending(min_percent=15)

    assert world.audit.records == []
    assert world.insight.updates == []

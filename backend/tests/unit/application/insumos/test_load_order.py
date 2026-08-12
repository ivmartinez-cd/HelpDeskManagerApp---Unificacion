"""Tests de caracterización del caso de uso LoadOrder (los 5 bloqueos + creación).

Usa los servicios de dominio REALES (CanalDirectoOrderCreation, SupplyMatchResolver,
ClaimedOrderCreation) sobre fakes de los puertos — el mismo alcance que cubría
test_requests_load.py del legacy contra su StateDb/SOAP mockeado.
"""

from datetime import UTC, datetime

from src.modules.insumos.application.dtos.load_order import (
    CONFLICT_ACTIVE_SUPPLY,
    CONFLICT_AMBIGUOUS_INSUMO,
    CONFLICT_PENDING_VALIDATION,
    CONFLICT_TODAY_ORDER,
    LoadOrderCommand,
)
from src.modules.insumos.application.use_cases._load_order_context import (
    LoadOrderConfig,
    LoadOrderPorts,
)
from src.modules.insumos.application.use_cases.load_order import LoadOrder
from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    EVENT_FAILED,
    ORDER_TYPE_INCIDENT,
    AuditRecord,
)
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CREATED,
    ProcessedRequest,
)
from src.modules.insumos.domain.services.claimed_order_creation import ClaimedOrderCreation
from src.modules.insumos.domain.services.incident_creation import CanalDirectoIncidentCreation
from src.modules.insumos.domain.services.order_creation import CanalDirectoOrderCreation
from src.modules.insumos.domain.services.supply_request_matching import SupplyMatchResolver
from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdSupply
from src.modules.insumos.domain.value_objects.pending_validation import PendingValidation
from tests.unit.domain.insumos.fakes import (
    FakeInsightGateway,
    FakeOrderAuditRepository,
    FakeOrderClaimRepository,
    FakeProcessedRequestRepository,
    FakeRequestValidationRepository,
    FakeSupplyCacheRepository,
    FakeWsAycGateway,
    FakeZoneContactRepository,
    settings,
)

_REQUEST_ID = 974325


class World:
    """Todos los fakes + el caso de uso armado con los servicios de dominio reales."""

    def __init__(self) -> None:
        self.insight = FakeInsightGateway()
        self.wsayc = FakeWsAycGateway()
        self.processed = FakeProcessedRequestRepository()
        self.audit = FakeOrderAuditRepository()
        self.validations = FakeRequestValidationRepository()
        self.zone_contacts = FakeZoneContactRepository()
        self.supply_cache = FakeSupplyCacheRepository()
        self.claims = FakeOrderClaimRepository()

        self.insight.consumable_requests = [
            {
                "id": _REQUEST_ID,
                "deviceId": 7,
                "requested": "2026-08-10T10:00:00.000Z",
                "consumable": {
                    "sku": "CF230A",
                    "description": "Cartucho negro HP 30A",
                    "percentLeft": 5.0,
                    "daysLeft": 3,
                    "pagesLeft": 120,
                    "reorderPart": {"type": "TONER"},
                    "type": "TONER",
                },
            }
        ]
        self.insight.devices_by_id[7] = {
            "deviceId": 7,
            "serialNumber": "SERIE1",
            "extendedFields": {"zone": "HANGAR"},
        }
        # La verificación post-creación tiene que ver NUESTRA referencia.
        self.wsayc.default_supply = CdSupply(
            supply_id=441770, reference=f"SDS-{_REQUEST_ID}", fecha="31/07/2026 10:00:00"
        )
        # Idem para el incidente de kit de mantenimiento (test_kit_de_mantenimiento_*).
        self.wsayc.incidents_by_id[self.wsayc.persist_incident_result] = CdSupply(
            supply_id=self.wsayc.persist_incident_result, reference=f"SDS-{_REQUEST_ID}"
        )

        cfg = settings()
        order_creation = CanalDirectoOrderCreation(
            self.wsayc, self.supply_cache, cfg, verify_delays=(0,)
        )
        incident_creation = CanalDirectoIncidentCreation(self.wsayc, cfg, verify_delays=(0,))
        ports = LoadOrderPorts(
            insight=self.insight,  # type: ignore[arg-type]
            processed=self.processed,
            audit=self.audit,
            validations=self.validations,
            zone_contacts=self.zone_contacts,
            supply_cache=self.supply_cache,
            claimed_creation=ClaimedOrderCreation(self.claims),
            order_creation=order_creation,
            incident_creation=incident_creation,
            match_resolver=SupplyMatchResolver(self.wsayc, self.supply_cache),
        )
        self.use_case = LoadOrder(ports, LoadOrderConfig(order_settings=cfg))


def _command(**overrides: object) -> LoadOrderCommand:
    base: dict[str, object] = {
        "hp_request_id": _REQUEST_ID,
        "customer_id": 8,
        "customer_name": "Cliente Test",
    }
    base.update(overrides)
    return LoadOrderCommand(**base)  # type: ignore[arg-type]


# --- camino feliz ----------------------------------------------------------------------


async def test_carga_ok_crea_registra_y_audita() -> None:
    world = World()

    result = await world.use_case.execute(_command())

    assert result.ok
    assert result.order_id == "441770-3"
    assert result.supply_url is not None and result.supply_url.endswith("/supplies/view/441770-3")
    processed = world.processed.rows[_REQUEST_ID]
    assert processed.status == STATUS_CREATED
    assert processed.initial_percent_left == 5
    created = [r for r in world.audit.records if r.event == EVENT_CREATED]
    assert len(created) == 1
    assert created[0].hp_request_time == datetime(2026, 8, 10, 10, 0, tzinfo=UTC)
    # El claim siempre se libera, haya salido bien o mal.
    assert world.claims.released == [("SERIE1", "CF230A")]


async def test_dry_run_no_persiste_pero_audita_como_simulacion() -> None:
    world = World()

    result = await world.use_case.execute(_command(dry_run=True))

    assert result.ok
    assert result.order_id == f"DRYRUN-SDS-{_REQUEST_ID}"
    assert result.supply_url is None
    assert world.wsayc.persisted_payloads == []  # nunca tocó el SOAP
    assert _REQUEST_ID not in world.processed.rows
    assert world.audit.records[0].dry_run is True


# --- resolución contra Insight ---------------------------------------------------------


async def test_insight_caido_devuelve_error_sin_crear() -> None:
    world = World()
    world.insight.requests_error = ConnectionError("timeout")

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert result.error is not None and "No se pudo verificar" in result.error


async def test_solicitud_inexistente_devuelve_error() -> None:
    world = World()
    world.insight.consumable_requests = []

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert result.error is not None and "no existe o ya no está pendiente" in result.error


async def test_consumible_ya_reemplazado_no_se_carga() -> None:
    world = World()
    world.insight.consumable_requests[0]["replacedDate"] = "2026-08-10T12:00:00.000Z"

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert result.error is not None and "ya fue reemplazado" in result.error


# --- bloqueo 0: ventana de validación --------------------------------------------------


async def test_validacion_pendiente_bloquea_y_force_override_la_saltea() -> None:
    world = World()
    world.validations.pending[_REQUEST_ID] = PendingValidation(
        hp_request_id=_REQUEST_ID,
        deadline_at=datetime(2026, 8, 10, 20, 0, tzinfo=UTC),
        initial_percent_left=0.0,
    )

    blocked = await world.use_case.execute(_command())
    assert not blocked.ok
    assert blocked.conflict_type == CONFLICT_PENDING_VALIDATION
    assert blocked.conflict_data["deadlineAt"] == "2026-08-10T20:00:00Z"

    forced = await world.use_case.execute(_command(force_override=True))
    assert forced.ok


# --- ya procesado (respuesta idempotente) ----------------------------------------------


async def test_ya_procesado_responde_idempotente_sin_crear() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(
            hp_request_id=_REQUEST_ID,
            device_serial="SERIE1",
            sku="CF230A",
            internal_order_id="441000-1",
        )
    )

    result = await world.use_case.execute(_command())

    assert result.ok
    assert result.order_id == "441000-1"
    assert world.wsayc.persisted_payloads == []


async def test_procesado_pero_anulado_en_cd_limpia_y_crea_uno_nuevo() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(
            hp_request_id=_REQUEST_ID,
            device_serial="SERIE1",
            sku="CF230A",
            internal_order_id="441000-1",
        )
    )
    await world.supply_cache.upsert(
        [CachedSupply(supply_id=441000, serial="SERIE1", estado="Anulado")]
    )

    result = await world.use_case.execute(_command())

    assert result.ok
    assert result.order_id == "441770-3"  # pedido nuevo, no el stale
    assert len(world.wsayc.persisted_payloads) == 1


# --- bloqueo 1: pedido de hoy ----------------------------------------------------------


async def test_pedido_de_hoy_bloquea_y_force_override_lo_saltea() -> None:
    world = World()
    await world.processed.mark_processed(
        ProcessedRequest(
            hp_request_id=111,
            device_serial="SERIE1",
            sku="CF230A",
            internal_order_id="441111-1",
            created_at=datetime.now(UTC),
        )
    )

    blocked = await world.use_case.execute(_command())
    assert blocked.conflict_type == CONFLICT_TODAY_ORDER
    assert blocked.conflict_data["orderId"] == "441111-1"

    forced = await world.use_case.execute(_command(force_override=True))
    assert forced.ok


# --- bloqueo 2: pedido activo en CD ----------------------------------------------------


async def test_pedido_activo_del_mismo_consumible_bloquea() -> None:
    world = World()
    await world.supply_cache.upsert(
        [
            CachedSupply(
                supply_id=441500,
                serial="SERIE1",
                estado="Pendiente",
                description="Cartucho negro HP 30A",
            )
        ]
    )

    result = await world.use_case.execute(_command())

    assert result.conflict_type == CONFLICT_ACTIVE_SUPPLY
    assert result.conflict_data["supplyId"] == "441500-6"
    assert result.conflict_data["estado"] == "Pendiente"


async def test_pedido_activo_de_otro_color_no_bloquea() -> None:
    """Bug 441448: el pedido activo de OTRO consumible de la serie no debe bloquear."""
    world = World()
    await world.supply_cache.upsert(
        [
            CachedSupply(
                supply_id=441448,
                serial="SERIE1",
                estado="Pendiente",
                description="Toner Cyan HP",
            )
        ]
    )

    result = await world.use_case.execute(_command())

    assert result.ok


async def test_dry_run_saltea_bloqueo_de_pedido_activo() -> None:
    """A diferencia de forceOverride, dry_run sí saltea este bloqueo (nunca toca SOAP,
    así que no hay riesgo real de duplicar el pedido activo)."""
    world = World()
    await world.supply_cache.upsert(
        [
            CachedSupply(
                supply_id=441500,
                serial="SERIE1",
                estado="Pendiente",
                description="Cartucho negro HP 30A",
            )
        ]
    )

    result = await world.use_case.execute(_command(dry_run=True))

    assert result.ok
    assert result.order_id == f"DRYRUN-SDS-{_REQUEST_ID}"
    assert world.wsayc.persisted_payloads == []


# --- bloqueo 3: tope diario (nunca bypasseable) ----------------------------------------


async def test_tope_diario_bloquea_incluso_con_force_override() -> None:
    world = World()
    for _ in range(3):
        await world.audit.record(AuditRecord(event=EVENT_CREATED, hp_request_id=_REQUEST_ID))

    result = await world.use_case.execute(_command(force_override=True))

    assert not result.ok
    assert result.error is not None and "3 veces hoy" in result.error


async def test_dry_run_saltea_tope_diario() -> None:
    """El tope cuenta cargas reales (`count_created_today` ignora filas dry-run, ver
    test de integración del repo) — permitir dry-run acá es consistente, no un agujero:
    nunca va a sumar al contador que el propio bloqueo mira."""
    world = World()
    for _ in range(3):
        await world.audit.record(AuditRecord(event=EVENT_CREATED, hp_request_id=_REQUEST_ID))

    result = await world.use_case.execute(_command(dry_run=True))

    assert result.ok
    assert result.order_id == f"DRYRUN-SDS-{_REQUEST_ID}"


# --- errores de creación ---------------------------------------------------------------


async def test_serie_no_activa_audita_failed_y_devuelve_error() -> None:
    world = World()
    world.wsayc.machine = None

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert result.error is not None and "no está activo en Canal Directo" in result.error
    failed = [r for r in world.audit.records if r.event == EVENT_FAILED]
    assert len(failed) == 1
    # El claim se liberó igual (el próximo intento no queda trabado).
    assert world.claims.released == [("SERIE1", "CF230A")]


async def test_insumo_ambiguo_devuelve_opciones_para_el_operador() -> None:
    world = World()
    world.wsayc.article_parts = {"1": "Option A", "2": "Option B"}
    world.insight.consumable_requests[0]["consumable"]["description"] = ""

    result = await world.use_case.execute(_command())

    assert result.conflict_type == CONFLICT_AMBIGUOUS_INSUMO
    assert result.insumo_options == [
        {"id": "1", "name": "Option A"},
        {"id": "2", "name": "Option B"},
    ]


async def test_kit_de_mantenimiento_crea_incidente_via_soap() -> None:
    """Los kits de mantenimiento van como incidente (persistNewIncident, tipo 101
    Correctivo — ver docstring de incident_creation.py) en vez de pedido de insumo."""
    world = World()
    world.insight.consumable_requests[0]["consumable"]["reorderPart"] = {
        "type": "MAINTENANCE_KIT"
    }

    result = await world.use_case.execute(_command())

    assert result.ok
    assert result.order_id == str(world.wsayc.persist_incident_result)
    assert result.supply_url is None  # los incidentes no tienen URL de vista propia
    assert world.wsayc.persisted_payloads == []  # nunca tocó persistNewSupply
    assert len(world.wsayc.persisted_incident_payloads) == 1
    payload = world.wsayc.persisted_incident_payloads[0]["Incident"]
    assert payload["NroSerie"] == "SERIE1"
    assert payload["NroIncidenteCliente"] == f"SDS-{_REQUEST_ID}"
    assert payload["Ingreso"] != "guardia"
    processed = world.processed.rows[_REQUEST_ID]
    assert processed.internal_order_id == str(world.wsayc.persist_incident_result)
    created = [r for r in world.audit.records if r.event == EVENT_CREATED]
    assert created[0].order_type == ORDER_TYPE_INCIDENT
    assert created[0].detail == "Pre-Correctivo (kit de mantenimiento)"


async def test_kit_de_mantenimiento_dry_run_no_persiste() -> None:
    world = World()
    world.insight.consumable_requests[0]["consumable"]["reorderPart"] = {
        "type": "MAINTENANCE_KIT"
    }

    result = await world.use_case.execute(_command(dry_run=True))

    assert result.ok
    assert result.order_id == f"DRYRUN-SDS-{_REQUEST_ID}"
    assert world.wsayc.persisted_incident_payloads == []
    assert _REQUEST_ID not in world.processed.rows


async def test_kit_de_mantenimiento_no_confirmado_audita_failed() -> None:
    world = World()
    world.insight.consumable_requests[0]["consumable"]["reorderPart"] = {
        "type": "MAINTENANCE_KIT"
    }
    world.wsayc.persist_incident_result = 0  # persistNewIncident no confirmó

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert _REQUEST_ID not in world.processed.rows
    failed = [r for r in world.audit.records if r.event == EVENT_FAILED]
    assert len(failed) == 1


async def test_kit_de_mantenimiento_no_verificado_no_marca_procesado() -> None:
    world = World()
    world.insight.consumable_requests[0]["consumable"]["reorderPart"] = {
        "type": "MAINTENANCE_KIT"
    }
    world.wsayc.incidents_by_id.clear()  # la relectura post-creación no lo encuentra

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert _REQUEST_ID not in world.processed.rows


async def test_claim_tomado_devuelve_error_de_negocio() -> None:
    world = World()
    await world.claims.try_claim("SERIE1", "CF230A")

    result = await world.use_case.execute(_command())

    assert not result.ok
    assert result.error is not None and "pedido en curso" in result.error

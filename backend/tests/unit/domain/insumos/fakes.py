"""Fakes compartidos de los puertos de insumos para tests unitarios."""

from collections.abc import Sequence
from dataclasses import asdict, replace
from datetime import UTC, date, datetime, timedelta

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CANCELLED,
    EVENT_CREATED,
    EVENT_RELEASED,
    AuditRecord,
    AuditSnapshot,
    StoredAuditRecord,
)
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.dismissed_supply import DismissedSupply
from src.modules.insumos.domain.entities.known_device import (
    MONITORED_STATUSES,
    DeviceInventoryEntry,
    KnownDevice,
)
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CREATED,
    ProcessedInitialSnapshot,
    ProcessedRequest,
)
from src.modules.insumos.domain.entities.request_alert import (
    STATE_ACKNOWLEDGED,
    STATE_ESCALATED,
    STATE_TRIGGERED,
    RequestAlert,
)
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.value_objects.audit_history import AuditClosures, AuditFilters
from src.modules.insumos.domain.value_objects.audit_statistics import (
    CustomerActivity,
    DailyEventCount,
    DeviceCount,
    DispatchRow,
    FailureReasonCount,
    FulfillmentRow,
    RecentFailure,
    SkuCount,
    SourceSplit,
)
from src.modules.insumos.domain.value_objects.cd_supply import (
    CachedSupply,
    CdIncident,
    CdMachine,
    CdSupply,
    SupplyStatusEvent,
)
from src.modules.insumos.domain.value_objects.client_order_notice import ClientOrderNotice
from src.modules.insumos.domain.value_objects.mail_log_entry import (
    MailLogEntry,
    MailLogRecord,
    MailMessage,
)
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_PENDING,
    PendingValidation,
    PendingValidationWork,
    ValidationStart,
)
from src.modules.insumos.domain.value_objects.zone_contacts import (
    Customer,
    ZoneContactRow,
    ZoneContacts,
)

HAPPY_MACHINE = CdMachine(
    familia_id="255", familia_name="HP E50145/52645", empresa_id="8", sucursal_id="13840"
)
HAPPY_VERIFIED = CdSupply(
    supply_id=441770, reference="SDS-123", fecha="31/07/2026 10:00:00"
)


def settings(**overrides: object) -> CanalDirectoOrderSettings:
    base: dict[str, object] = {
        "solicitante": ContactInfo(
            apellido="Gomez",
            nombre="Juan",
            telefono="1140004000",
            email="sol@e.com",
            sector="Sistemas",
        ),
        "destinatario": ContactInfo(
            apellido="Perez",
            nombre="Ana",
            telefono="1150005000",
            email="dest@e.com",
            sector="Depósito",
        ),
        "origen_id": "6",
        "motivo_id": "1",
    }
    base.update(overrides)
    return CanalDirectoOrderSettings(**base)  # type: ignore[arg-type]


class FakeWsAycGateway:
    """Respuestas configurables por atributo; registra las llamadas que importan."""

    def __init__(self) -> None:
        self.machine: CdMachine | None = HAPPY_MACHINE
        self.machine_error: Exception | None = None
        self.article_parts: dict[str, str] = {"3729": "HP E50145/52645 - Toner"}
        self.persist_result = 441770
        self.persisted_payloads: list[dict[str, object]] = []
        self.persist_incident_result = 840020
        self.persisted_incident_payloads: list[dict[str, object]] = []
        # fetch_supply_by_id: primero consume supply_reads en orden; si se agotó, usa
        # supplies_by_id (keyed) o default_supply.
        self.supply_reads: list[CdSupply | None] = []
        self.supplies_by_id: dict[int, CdSupply] | None = None
        self.default_supply: CdSupply | None = HAPPY_VERIFIED
        self.fetch_calls: list[int] = []
        self.supplies_for_empresa: list[CdSupply] = []
        self.description = "HP E50145/52645 - Toner"
        # Si está seteado, get_supply_description responde por ID ("" si no está).
        self.descriptions_by_id: dict[int, str] | None = None
        self.description_calls: list[int] = []
        self.incidents_by_id: dict[int, CdSupply] = {}
        self.incident_calls: list[int] = []
        self.machine_incidents: list[CdIncident] = []
        self.void_supply_result = True
        self.void_incident_result = True
        self.voided_supplies: list[int] = []
        self.voided_incidents: list[int] = []

    async def get_machine_by_serial(self, serial: str) -> CdMachine | None:
        if self.machine_error is not None:
            raise self.machine_error
        return self.machine

    async def get_machine_incidents(self, machine_id: str, top: int = 3) -> list[CdIncident]:
        return self.machine_incidents

    async def get_article_parts(self, familia_id: str) -> dict[str, str]:
        return self.article_parts

    async def persist_new_supply(self, payload: dict[str, object]) -> int:
        self.persisted_payloads.append(payload)
        return self.persist_result

    async def fetch_supply_by_id(self, supply_id: int) -> CdSupply | None:
        self.fetch_calls.append(supply_id)
        if self.supply_reads:
            return self.supply_reads.pop(0)
        if self.supplies_by_id is not None:
            return self.supplies_by_id.get(supply_id)
        return self.default_supply

    async def persist_new_incident(self, payload: dict[str, object]) -> int:
        self.persisted_incident_payloads.append(payload)
        return self.persist_incident_result

    async def fetch_incident_by_id(self, incident_id: int) -> CdSupply | None:
        self.incident_calls.append(incident_id)
        return self.incidents_by_id.get(incident_id)

    async def get_supply_description(self, supply_id: int) -> str:
        self.description_calls.append(supply_id)
        if self.descriptions_by_id is not None:
            return self.descriptions_by_id.get(supply_id, "")
        return self.description

    async def get_supplies_for_empresa(
        self, empresa_id: str, sucursal_id: str = "", top: str = "200"
    ) -> list[CdSupply]:
        return self.supplies_for_empresa

    async def void_supply(self, supply_id: int) -> bool:
        self.voided_supplies.append(supply_id)
        return self.void_supply_result

    async def void_incident(self, incident_id: int) -> bool:
        self.voided_incidents.append(incident_id)
        return self.void_incident_result


class FakeSupplyCacheRepository:
    def __init__(self) -> None:
        self.entries: list[CachedSupply] = []
        self.get_error: Exception | None = None
        self.recently_cached: set[int] = set()
        self.status_history: dict[int, list[SupplyStatusEvent]] = {}

    async def upsert(self, entries: list[CachedSupply]) -> None:
        self.entries.extend(entries)

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        if self.get_error is not None:
            raise self.get_error
        matching = [e for e in self.entries if e.serial.upper() == serial.upper()]
        return sorted(matching, key=lambda e: e.supply_id, reverse=True)[:limit]

    async def find_active_by_serial(self, serial: str) -> CachedSupply | None:
        active = [
            e
            for e in await self.get_by_serial(serial)
            if e.estado not in ("Entregado", "Anulado", "Cancelado")
        ]
        return active[0] if active else None

    async def get_status(self, supply_id: int) -> str | None:
        return next((e.estado for e in self.entries if e.supply_id == supply_id), None)

    async def get_statuses_batch(self, supply_ids: list[int]) -> dict[int, str]:
        return {
            e.supply_id: e.estado
            for e in self.entries
            if e.supply_id in set(supply_ids) and e.estado
        }

    async def get_recently_cached_ids(
        self, supply_ids: list[int], within_seconds: int
    ) -> set[int]:
        return self.recently_cached & set(supply_ids)

    async def get_noncancelled_by_serials(
        self, serials: list[str]
    ) -> dict[str, list[CachedSupply]]:
        result: dict[str, list[CachedSupply]] = {}
        for serial in serials:
            rows = [
                e
                for e in await self.get_by_serial(serial, limit=1000)
                if e.estado not in ("Anulado", "Cancelado")
            ]
            if rows:
                result[serial.upper()] = rows
        return result

    async def get_status_history_batch(
        self, supply_ids: list[int]
    ) -> dict[int, list[SupplyStatusEvent]]:
        return {sid: self.status_history[sid] for sid in supply_ids if sid in self.status_history}


class FakeCustomerConfigRepository:
    def __init__(self) -> None:
        self.customers: list[CustomerConfig] = []

    async def list_enabled(self) -> list[CustomerConfig]:
        return [c for c in self.customers if c.enabled]

    async def get_names(self) -> dict[int, str]:
        return {c.customer_id: c.name for c in self.customers}

    async def sync_discovered(self, customers: list[CustomerConfig]) -> None:
        by_id = {c.customer_id: c for c in self.customers}
        for incoming in customers:
            existing = by_id.get(incoming.customer_id)
            # El `enabled` de un cliente ya registrado nunca se pisa.
            by_id[incoming.customer_id] = (
                replace(existing, name=incoming.name) if existing else incoming
            )
        self.customers = list(by_id.values())


class FakeInsumosSettingsRepository:
    def __init__(self) -> None:
        self.raw: dict[str, str] = {}

    async def get_all(self) -> dict[str, str]:
        return dict(self.raw)

    async def set_all(self, values: dict[str, str]) -> None:
        self.raw.update(values)


class FakeOrderClaimRepository:
    def __init__(self) -> None:
        self._claimed: set[tuple[str, str]] = set()
        self.released: list[tuple[str, str]] = []

    async def try_claim(self, device_serial: str, sku: str) -> bool:
        key = (device_serial, sku)
        if key in self._claimed:
            return False
        self._claimed.add(key)
        return True

    async def release(self, device_serial: str, sku: str) -> None:
        self._claimed.discard((device_serial, sku))
        self.released.append((device_serial, sku))


class FakeProcessedRequestRepository:
    """En memoria; el "hoy" no filtra por fecha — todo lo insertado cuenta como de hoy
    (los cortes reales de día argentino se prueban en integración)."""

    def __init__(self) -> None:
        self.rows: dict[int, ProcessedRequest] = {}

    async def get(self, hp_request_id: int) -> ProcessedRequest | None:
        return self.rows.get(hp_request_id)

    async def mark_processed(self, request: ProcessedRequest) -> None:
        self.rows[request.hp_request_id] = request

    async def mark_cancelled(self, hp_request_id: int) -> None:
        row = self.rows[hp_request_id]
        self.rows[hp_request_id] = ProcessedRequest(
            hp_request_id=row.hp_request_id,
            status="CANCELLED",
            device_serial=row.device_serial,
            sku=row.sku,
            internal_order_id=row.internal_order_id,
        )

    async def get_today_order_for(self, device_serial: str, sku: str) -> ProcessedRequest | None:
        return next(
            (
                r
                for r in self.rows.values()
                if r.device_serial == device_serial
                and r.sku == sku
                and r.status == STATUS_CREATED
            ),
            None,
        )

    async def get_created_by_serial(self, device_serial: str) -> list[ProcessedRequest]:
        return [
            r
            for r in self.rows.values()
            if r.device_serial.upper() == device_serial.upper() and r.status == STATUS_CREATED
        ]

    async def get_processed_ids(self, hp_request_ids: list[int]) -> set[int]:
        return {
            rid
            for rid in hp_request_ids
            if rid in self.rows and self.rows[rid].status == STATUS_CREATED
        }

    async def get_supply_ids(self, hp_request_ids: list[int]) -> dict[int, int]:
        result: dict[int, int] = {}
        for rid in hp_request_ids:
            row = self.rows.get(rid)
            if row is None or row.status != STATUS_CREATED:
                continue
            if row.internal_order_id.startswith("DRYRUN"):
                continue
            try:
                result[rid] = int(row.internal_order_id.split("-")[0])
            except (ValueError, IndexError):
                continue
        return result

    async def get_today_processed_ids(self, hp_request_ids: list[int]) -> set[int]:
        # En el fake todo lo insertado cuenta como "de hoy".
        return await self.get_processed_ids(hp_request_ids)

    async def count_processed_today(self) -> int:
        return len([r for r in self.rows.values() if r.status == STATUS_CREATED])

    async def get_created_by_serials(
        self, device_serials: list[str]
    ) -> dict[str, list[ProcessedRequest]]:
        result: dict[str, list[ProcessedRequest]] = {}
        for serial in device_serials:
            rows = await self.get_created_by_serial(serial)
            if rows:
                result[serial.upper()] = rows
        return result

    async def get_all_created(self, customer_id: int | None = None) -> list[ProcessedRequest]:
        return [
            r
            for r in self.rows.values()
            if r.status == STATUS_CREATED
            and (customer_id is None or r.customer_id == customer_id)
        ]

    async def backfill_initial_snapshot(
        self, updates: list[ProcessedInitialSnapshot]
    ) -> None:
        for entry in updates:
            row = self.rows.get(entry.hp_request_id)
            if row is None:
                continue
            self.rows[entry.hp_request_id] = replace(
                row,
                initial_percent_left=entry.initial_percent_left,
                initial_days_left=entry.initial_days_left,
                initial_pages_left=entry.initial_pages_left,
            )


def _matches_audit_filters(record: StoredAuditRecord, filters: AuditFilters) -> bool:
    """Filtrado en memoria equivalente a `_conditions` del adaptador SQL — sin
    reproducir el escape de LIKE (esa fidelidad fina se cubre en integración)."""
    if filters.events is not None and record.event not in filters.events:
        return False
    if record.created_at is not None:
        day = record.created_at.date()
        if filters.start_day is not None and day < filters.start_day:
            return False
        if filters.end_day is not None and day > filters.end_day:
            return False
    if filters.search:
        term = filters.search.lower()
        haystack = (
            record.customer_name,
            record.device_serial,
            record.sku,
            record.description,
            record.internal_order_id,
            record.detail,
        )
        if not any(term in (value or "").lower() for value in haystack):
            return False
    return True


class FakeOrderAuditRepository:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []
        self.stored: list[StoredAuditRecord] = []
        self.backfills: list[AuditSnapshot] = []
        self.closures_for_calls: list[Sequence[int]] = []

    async def record(self, entry: AuditRecord) -> None:
        self.records.append(entry)
        self.stored.append(
            StoredAuditRecord(
                audit_id=len(self.stored) + 1,
                created_at=datetime.now(UTC),
                **asdict(entry),
            )
        )

    async def count_created_today(self, hp_request_id: int) -> int:
        return len(
            [
                r
                for r in self.records
                if r.event == EVENT_CREATED
                and r.hp_request_id == hp_request_id
                and not r.dry_run
            ]
        )

    async def list_page(
        self, filters: AuditFilters, limit: int, offset: int
    ) -> list[StoredAuditRecord]:
        matched = [r for r in reversed(self.stored) if _matches_audit_filters(r, filters)]
        return matched[offset : offset + limit]

    async def count(self, filters: AuditFilters) -> int:
        return len([r for r in self.stored if _matches_audit_filters(r, filters)])

    async def count_by_event(self, filters: AuditFilters) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.stored:
            if _matches_audit_filters(record, filters):
                counts[record.event] = counts.get(record.event, 0) + 1
        return counts

    async def closures_for(self, hp_request_ids: Sequence[int]) -> AuditClosures:
        self.closures_for_calls.append(hp_request_ids)
        ids = set(hp_request_ids)
        last_created: dict[int, int] = {}
        last_closed: dict[int, int] = {}
        for record in self.stored:
            if record.hp_request_id is None or record.hp_request_id not in ids:
                continue
            if record.event == EVENT_CREATED:
                last_created[record.hp_request_id] = max(
                    last_created.get(record.hp_request_id, 0), record.audit_id
                )
            elif record.event in (EVENT_CANCELLED, EVENT_RELEASED):
                last_closed[record.hp_request_id] = max(
                    last_closed.get(record.hp_request_id, 0), record.audit_id
                )
        return AuditClosures(last_created=last_created, last_closed=last_closed)

    async def backfill_snapshots(self, updates: list[AuditSnapshot]) -> None:
        self.backfills.extend(updates)
        for entry in updates:
            index = entry.audit_id - 1
            self.stored[index] = replace(
                self.stored[index],
                device_id=entry.device_id,
                initial_percent_left=entry.initial_percent_left,
                initial_days_left=entry.initial_days_left,
                initial_pages_left=entry.initial_pages_left,
            )


class FakeRequestValidationRepository:
    """Lectura + escritura en memoria. La semántica fina del UPSERT (no reiniciar el
    reloj, no pisar un status resuelto) se prueba en integración contra Postgres —
    acá alcanza con el contrato que consumen los casos de uso."""

    def __init__(self) -> None:
        self.pending: dict[int, PendingValidation] = {}
        self.swap_notes: dict[int, str] = {}
        self.statuses: dict[int, str] = {}
        self.diagnosed: set[int] = set()
        self.starts: list[ValidationStart] = []
        self.work: dict[int, PendingValidationWork] = {}
        self.resolved: list[tuple[int, str]] = []

    async def get_pending(self, hp_request_id: int) -> PendingValidation | None:
        return self.pending.get(hp_request_id)

    async def get_swap_note(self, hp_request_id: int) -> str | None:
        return self.swap_notes.get(hp_request_id)

    async def get_pending_ids(self, hp_request_ids: list[int]) -> set[int]:
        return {rid for rid in hp_request_ids if rid in self.pending}

    async def get_pending_batch(
        self, hp_request_ids: list[int]
    ) -> dict[int, PendingValidation]:
        return {rid: self.pending[rid] for rid in hp_request_ids if rid in self.pending}

    async def is_diagnosed(self, hp_request_id: int) -> bool:
        return hp_request_id in self.diagnosed

    async def start(self, data: ValidationStart) -> None:
        self.starts.append(data)
        self.diagnosed.add(data.hp_request_id)
        if data.swap_note:
            self.swap_notes[data.hp_request_id] = data.swap_note
        if data.hp_request_id in self.statuses:
            return  # la fila ya existía: no reinicia el reloj ni pisa el status
        self.statuses[data.hp_request_id] = VALIDATION_PENDING
        self.pending[data.hp_request_id] = PendingValidation(
            hp_request_id=data.hp_request_id,
            deadline_at=datetime.now(UTC) + timedelta(minutes=data.deadline_minutes),
            initial_percent_left=data.initial_percent_left,
            diagnosis_headline=data.diagnosis_headline,
            diagnosis_detail=data.diagnosis_detail,
            swap_note=data.swap_note,
        )
        self.work[data.hp_request_id] = PendingValidationWork(
            hp_request_id=data.hp_request_id,
            customer_id=data.customer_id,
            device_id=data.device_id,
            device_serial=data.device_serial,
            sku=data.sku,
            initial_percent_left=data.initial_percent_left,
            is_due=data.deadline_minutes <= 0,
        )

    async def resolve(self, hp_request_id: int, status: str) -> bool:
        if self.statuses.get(hp_request_id) != VALIDATION_PENDING:
            return False
        self.statuses[hp_request_id] = status
        self.pending.pop(hp_request_id, None)
        self.work.pop(hp_request_id, None)
        self.resolved.append((hp_request_id, status))
        return True

    async def get_all_pending(self) -> list[PendingValidationWork]:
        return list(self.work.values())


class FakeZoneContactRepository:
    def __init__(self) -> None:
        self.zones: dict[tuple[int, str], ZoneContacts] = {}

    async def get(self, customer_id: int, zone: str) -> ZoneContacts | None:
        return self.zones.get((customer_id, zone))

    async def list_all(self, customer_id: int) -> list[ZoneContactRow]:
        return [
            ZoneContactRow(
                zone=zone,
                sol_apellido=contacts.solicitante.apellido,
                sol_nombre=contacts.solicitante.nombre,
                observaciones=contacts.observaciones,
            )
            for (cid, zone), contacts in self.zones.items()
            if cid == customer_id
        ]


class FakeInsightGateway:
    """Solo los métodos que usa LoadOrder; el resto no existe a propósito."""

    def __init__(self) -> None:
        self.consumable_requests: list[JsonDict] = []
        # Si está seteado, cada cliente tiene su propia lista (tests de dashboard).
        self.requests_by_customer: dict[int, list[JsonDict]] | None = None
        # Solicitudes ya resueltas (workflow_status="ACTIONED") por cliente.
        self.actioned_by_customer: dict[int, list[JsonDict]] = {}
        self.requests_error: Exception | None = None
        self.errors_by_customer: dict[int, Exception] = {}
        self.devices_by_id: dict[int, JsonDict] = {}
        self.updates: list[JsonDict] = []
        self.update_error: Exception | None = None
        self.consumables_by_device: dict[int, list[JsonDict]] = {}
        self.consumables_error: Exception | None = None
        self.history_by_device: dict[int, list[JsonDict]] = {}
        self.history_error: Exception | None = None
        # Si está seteado, cada workflowStatus tiene su propia lista (historial del modal).
        self.requests_by_status: dict[str, list[JsonDict]] | None = None
        self.alerts_by_device: dict[int, list[JsonDict]] = {}
        self.alerts_error: Exception | None = None
        self.customers: list[JsonDict] = []
        self.customers_error: Exception | None = None
        self.inventory_by_customer: dict[int, list[JsonDict]] = {}
        self.inventory_errors: dict[int, Exception] = {}

    async def get_customers(self) -> list[JsonDict]:
        if self.customers_error is not None:
            raise self.customers_error
        return list(self.customers)

    async def get_devices(self, customer_id: int) -> list[JsonDict]:
        if customer_id in self.inventory_errors:
            raise self.inventory_errors[customer_id]
        return list(self.inventory_by_customer.get(customer_id, []))

    async def get_consumable_requests(
        self,
        customer_id: int,
        workflow_status: str = "OUTSTANDING",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[JsonDict]:
        if self.requests_error is not None:
            raise self.requests_error
        if customer_id in self.errors_by_customer:
            raise self.errors_by_customer[customer_id]
        if self.requests_by_status is not None:
            return self.requests_by_status.get(workflow_status, [])
        if workflow_status == "ACTIONED":
            return self.actioned_by_customer.get(customer_id, [])
        if self.requests_by_customer is not None:
            return self.requests_by_customer.get(customer_id, [])
        return self.consumable_requests

    async def get_device_by_id(self, device_id: int) -> JsonDict:
        return self.devices_by_id.get(device_id, {})

    async def get_device_consumables(self, device_id: int) -> list[JsonDict]:
        if self.consumables_error is not None:
            raise self.consumables_error
        return self.consumables_by_device.get(device_id, [])

    async def get_consumable_history(
        self,
        device_id: int,
        consumable_index: int,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[JsonDict]:
        if self.history_error is not None:
            raise self.history_error
        return self.history_by_device.get(device_id, [])

    async def get_device_alerts_history(
        self,
        device_id: int,
        alert_classes: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        max_results: int | None = None,
    ) -> list[JsonDict]:
        if self.alerts_error is not None:
            raise self.alerts_error
        return self.alerts_by_device.get(device_id, [])

    async def update_consumable_request(
        self,
        request_id: int,
        external_ref: str | None = None,
        status_update: str | None = None,
        comment: str | None = None,
    ) -> JsonDict:
        if self.update_error is not None:
            raise self.update_error
        self.updates.append(
            {
                "request_id": request_id,
                "externalRef": external_ref,
                "statusUpdate": status_update,
                "comment": comment,
            }
        )
        return {"ok": True}


class FakeAuditStatisticsRepository:
    """Agregados pre-sembrados por atributo: la traducción a SQL se verifica en
    integración, acá interesa qué hace el caso de uso con lo que le devuelven.
    `totals_by_range` es un dict a propósito — deja aseverar que el período previo se
    consultó con el rango exacto y no con el actual."""

    def __init__(self) -> None:
        self.earliest: date | None = None
        self.names: dict[int, str] = {}
        self.counts: list[DailyEventCount] = []
        self.totals_by_range: dict[tuple[date, date], dict[str, int]] = {}
        self.customers: list[CustomerActivity] = []
        self.skus: list[SkuCount] = []
        self.devices: list[DeviceCount] = []
        self.reasons: list[FailureReasonCount] = []
        self.failures: list[RecentFailure] = []
        self.split = SourceSplit(auto=0, total=0)
        self.fulfillment: list[FulfillmentRow] = []
        self.dispatch: list[DispatchRow] = []
        self.totals_calls: list[tuple[date, date, int | None]] = []

    async def earliest_day(self) -> date | None:
        return self.earliest

    async def customer_name(self, customer_id: int) -> str | None:
        return self.names.get(customer_id)

    async def daily_counts(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[DailyEventCount]:
        return list(self.counts)

    async def event_totals(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> dict[str, int]:
        self.totals_calls.append((start, end, customer_id))
        return dict(self.totals_by_range.get((start, end), {}))

    async def customer_activity(self, start: date, end: date) -> list[CustomerActivity]:
        return list(self.customers)

    async def top_skus(
        self, start: date, end: date, *, customer_id: int | None = None
    ) -> list[SkuCount]:
        return list(self.skus)

    async def top_devices(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[DeviceCount]:
        return self.devices[:limit]

    async def failure_reasons(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[FailureReasonCount]:
        return self.reasons[:limit]

    async def recent_failures(
        self, start: date, end: date, customer_id: int, limit: int
    ) -> list[RecentFailure]:
        return self.failures[:limit]

    async def source_split(self, start: date, end: date, customer_id: int) -> SourceSplit:
        return self.split

    async def fulfillment_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[FulfillmentRow]:
        return list(self.fulfillment)

    async def dispatch_rows(
        self, start: date, end: date, customer_id: int
    ) -> list[DispatchRow]:
        return list(self.dispatch)


class FakeKnownDeviceRepository:
    """Inventario en memoria. `enabled_customers` modela el INNER JOIN con
    customers_config que hace el listado de pendientes."""

    def __init__(self) -> None:
        self.monitored: dict[int, int] = {}
        self.devices: dict[int, KnownDevice] = {}
        self.enabled_customers: set[int] = set()
        self.pruned: list[tuple[int, tuple[int, ...]]] = []

    def add(self, device_id: int, **overrides: object) -> KnownDevice:
        base: dict[str, object] = {
            "device_id": device_id,
            "customer_id": 8,
            "customer_name": "Cliente Test",
            "serial": f"SERIE{device_id}",
            "model": "HP E50145",
            "zone": "Sucursal",
            "ip_address": "10.0.0.1",
            "monitor_status": "N",
            "discovery_date": None,
            "last_contact": None,
            "first_seen_at": datetime.now(UTC),
            "dismissed": False,
        }
        base.update(overrides)
        device = KnownDevice(**base)  # type: ignore[arg-type]
        self.devices[device_id] = device
        self.enabled_customers.add(device.customer_id)
        return device

    async def count_monitored_by_customer(self) -> dict[int, int]:
        return dict(self.monitored)

    async def list_pending(self) -> list[KnownDevice]:
        pending = [
            d
            for d in self.devices.values()
            if d.monitor_status not in MONITORED_STATUSES
            and d.customer_id in self.enabled_customers
        ]
        return sorted(pending, key=lambda d: d.device_id, reverse=True)

    async def count_pending(self) -> int:
        return len([d for d in await self.list_pending() if not d.dismissed])

    async def set_dismissed(self, device_id: int, dismissed: bool) -> bool:
        device = self.devices.get(device_id)
        if device is None:
            return False
        self.devices[device_id] = replace(device, dismissed=dismissed)
        return True

    async def upsert(self, entries: list[DeviceInventoryEntry]) -> list[int]:
        new_ids = [e.device_id for e in entries if e.device_id not in self.devices]
        for entry in entries:
            self.add(
                entry.device_id,
                customer_id=entry.customer_id,
                serial=entry.serial,
                model=entry.model,
                zone=entry.zone,
                ip_address=entry.ip_address,
                monitor_status=entry.monitor_status,
                discovery_date=entry.discovery_date,
                last_contact=entry.last_contact,
            )
        return new_ids

    async def prune_missing(self, customer_id: int, present_device_ids: list[int]) -> int:
        self.pruned.append((customer_id, tuple(present_device_ids)))
        stale = [
            device_id
            for device_id, device in self.devices.items()
            if device.customer_id == customer_id and device_id not in present_device_ids
        ]
        for device_id in stale:
            del self.devices[device_id]
        return len(stale)


class FakeMailLogRepository:
    """Orden de inserción = orden cronológico; el listado devuelve el inverso."""

    def __init__(self) -> None:
        self.entries: list[MailLogEntry] = []
        self.records: list[MailLogRecord] = []

    def add(self, kind: str, subject: str, success: bool = True) -> MailLogEntry:
        entry = MailLogEntry(
            entry_id=len(self.entries) + 1,
            kind=kind,
            recipients="logistica@example.com",
            subject=subject,
            success=success,
            error=None if success else "SMTP timeout",
            sent_at=datetime.now(UTC),
        )
        self.entries.append(entry)
        return entry

    async def list_latest(self, limit: int, offset: int = 0) -> list[MailLogEntry]:
        latest_first = list(reversed(self.entries))
        return latest_first[offset : offset + limit]

    async def count(self) -> int:
        return len(self.entries)

    async def record(self, entry: MailLogRecord) -> None:
        self.records.append(entry)


class FakeMailer:
    """Manda de a uno, como el `Mailer` real. `fail_for` son direcciones que
    deben fallar (levanta una excepción genérica, como haría un timeout de SMTP)."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []
        self.fail_for: set[str] = set()

    async def send(self, *, to: str, subject: str, body: str) -> None:
        if to in self.fail_for:
            raise RuntimeError(f"SMTP timeout enviando a {to}")
        self.sent.append((to, subject, body))


class FakeMailDispatcher:
    """Registra los MailMessage despachados. `should_raise` simula que el
    dispatcher real revienta — para probar que quien lo llama no propaga
    (contrato de MailDispatcher.dispatch: nunca propaga)."""

    def __init__(self) -> None:
        self.dispatched: list[MailMessage] = []
        self.should_raise = False

    async def dispatch(self, message: MailMessage) -> None:
        if self.should_raise:
            raise RuntimeError("mail_dispatch: fallo simulado")
        self.dispatched.append(message)


class FakeRequestAlertRepository:
    """Alertas en memoria con su estado; el `now` de las transiciones no importa acá
    (los cortes reales se prueban en integración)."""

    def __init__(self) -> None:
        self.alerts: dict[int, RequestAlert] = {}
        self.states: dict[int, str] = {}
        self.escalate_calls: list[datetime] = []

    def add(self, hp_request_id: int, state: str, requested_at: datetime | None) -> None:
        self.alerts[hp_request_id] = RequestAlert(
            hp_request_id=hp_request_id,
            customer_id=8,
            customer_name="Cliente Test",
            device_serial=f"SERIE{hp_request_id}",
            sku="CF230A",
            description="Toner negro",
            requested_at=requested_at,
            first_seen_at=datetime.now(UTC),
            escalated_at=datetime.now(UTC) if state == STATE_ESCALATED else None,
        )
        self.states[hp_request_id] = state

    async def escalate_due(self, cutoff: datetime) -> int:
        self.escalate_calls.append(cutoff)
        escalated = 0
        for hp_request_id, alert in self.alerts.items():
            if self.states[hp_request_id] != STATE_TRIGGERED:
                continue
            if alert.requested_at is None or alert.requested_at > cutoff:
                continue
            self.states[hp_request_id] = STATE_ESCALATED
            self.alerts[hp_request_id] = replace(alert, escalated_at=datetime.now(UTC))
            escalated += 1
        return escalated

    async def list_escalated(self) -> list[RequestAlert]:
        escalated = [
            alert
            for hp_request_id, alert in self.alerts.items()
            if self.states[hp_request_id] == STATE_ESCALATED
        ]
        return sorted(escalated, key=lambda a: a.hp_request_id)

    async def acknowledge(self, hp_request_ids: list[int]) -> int:
        acknowledged = [
            hp_request_id
            for hp_request_id in hp_request_ids
            if self.states.get(hp_request_id) == STATE_ESCALATED
        ]
        for hp_request_id in acknowledged:
            self.states[hp_request_id] = STATE_ACKNOWLEDGED
        return len(acknowledged)


class FakeCustomerRepository:
    """CustomerRepository (pantalla Clientes) — distinto de FakeCustomerConfigRepository
    (list_enabled/get_names/sync_discovered), usado por LoadOrder para chequear
    is_client_mail_enabled antes de avisar al cliente."""

    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}

    async def list_all(self) -> list[Customer]:
        return list(self.customers.values())

    async def set_enabled(self, customer_id: int, enabled: bool) -> None:
        c = self.customers[customer_id]
        self.customers[customer_id] = replace(c, enabled=enabled)

    async def bulk_toggle(self, enabled: bool) -> None:
        self.customers = {cid: replace(c, enabled=enabled) for cid, c in self.customers.items()}

    async def set_client_mail_enabled(self, customer_id: int, enabled: bool) -> None:
        c = self.customers.get(customer_id)
        if c is None:
            return
        self.customers[customer_id] = replace(c, client_mail_enabled=enabled)

    async def is_client_mail_enabled(self, customer_id: int) -> bool:
        c = self.customers.get(customer_id)
        return bool(c and c.client_mail_enabled)

    async def sync(self, customers: list[dict[str, object]]) -> None:
        for entry in customers:
            cid = int(entry["customerId"])  # type: ignore[arg-type]
            if cid not in self.customers:
                self.customers[cid] = Customer(
                    customer_id=cid, name=str(entry["name"]), enabled=False
                )


class FakeDismissedSupplyRepository:
    def __init__(self) -> None:
        self.entries: dict[int, DismissedSupply] = {}

    async def mark_dismissed(
        self, supply_id: int, device_serial: str, hp_request_id: int | None = None
    ) -> None:
        if supply_id in self.entries:
            return
        self.entries[supply_id] = DismissedSupply(
            supply_id=supply_id, device_serial=device_serial, hp_request_id=hp_request_id
        )

    async def get_dismissed_ids(self, supply_ids: list[int]) -> set[int]:
        return {sid for sid in supply_ids if sid in self.entries}

    async def get_all_dismissed_ids(self) -> set[int]:
        return set(self.entries)

    async def get_pending_unignore(self) -> list[DismissedSupply]:
        return [e for e in self.entries.values() if e.hp_request_id is not None]

    async def clear(self, supply_id: int) -> None:
        self.entries.pop(supply_id, None)


class FakeDispatchUnconfirmedNotificationRepository:
    def __init__(self) -> None:
        self.notified: set[int] = set()

    async def get_notified_ids(self, hp_request_ids: list[int]) -> set[int]:
        return {rid for rid in hp_request_ids if rid in self.notified}

    async def mark_notified(self, hp_request_ids: list[int]) -> None:
        self.notified.update(hp_request_ids)


class FakeClientOrderNotifier:
    def __init__(self) -> None:
        self.notices: list[ClientOrderNotice] = []
        self.raise_error = False

    async def notify(self, notice: ClientOrderNotice) -> None:
        if self.raise_error:
            raise RuntimeError("smtp caído")
        self.notices.append(notice)

"""Fakes compartidos de los puertos de insumos para tests unitarios."""

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta

from src.modules.insumos.domain.entities.audit_record import (
    EVENT_CREATED,
    AuditRecord,
    AuditSnapshot,
    StoredAuditRecord,
)
from src.modules.insumos.domain.entities.customer_config import CustomerConfig
from src.modules.insumos.domain.entities.processed_request import (
    STATUS_CREATED,
    ProcessedRequest,
)
from src.modules.insumos.domain.repositories.insight_gateway import JsonDict
from src.modules.insumos.domain.value_objects.cd_supply import (
    CachedSupply,
    CdIncident,
    CdMachine,
    CdSupply,
)
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings
from src.modules.insumos.domain.value_objects.pending_validation import (
    VALIDATION_PENDING,
    PendingValidation,
    PendingValidationWork,
    ValidationStart,
)
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts

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
        "origen_id": "3",
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
        # fetch_supply_by_id: primero consume supply_reads en orden; si se agotó, usa
        # supplies_by_id (keyed) o default_supply.
        self.supply_reads: list[CdSupply | None] = []
        self.supplies_by_id: dict[int, CdSupply] | None = None
        self.default_supply: CdSupply | None = HAPPY_VERIFIED
        self.fetch_calls: list[int] = []
        self.supplies_for_empresa: list[CdSupply] = []
        self.description = "HP E50145/52645 - Toner"
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

    async def fetch_incident_by_id(self, incident_id: int) -> CdSupply | None:
        self.incident_calls.append(incident_id)
        return self.incidents_by_id.get(incident_id)

    async def get_supply_description(self, supply_id: int) -> str:
        self.description_calls.append(supply_id)
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


class FakeCustomerConfigRepository:
    def __init__(self) -> None:
        self.customers: list[CustomerConfig] = []

    async def list_enabled(self) -> list[CustomerConfig]:
        return [c for c in self.customers if c.enabled]


class FakeInsumosSettingsRepository:
    def __init__(self) -> None:
        self.raw: dict[str, str] = {}

    async def get_all(self) -> dict[str, str]:
        return dict(self.raw)


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


class FakeOrderAuditRepository:
    def __init__(self) -> None:
        self.records: list[AuditRecord] = []
        self.stored: list[StoredAuditRecord] = []
        self.backfills: list[AuditSnapshot] = []

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

    async def list_latest(self, limit: int, offset: int = 0) -> list[StoredAuditRecord]:
        latest_first = list(reversed(self.stored))
        return latest_first[offset : offset + limit]

    async def count(self) -> int:
        return len(self.stored)

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

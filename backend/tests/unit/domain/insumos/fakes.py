"""Fakes compartidos de los puertos de insumos para tests unitarios de dominio."""

from src.modules.insumos.domain.value_objects.cd_supply import CachedSupply, CdMachine, CdSupply
from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.order_settings import CanalDirectoOrderSettings

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

    async def get_machine_by_serial(self, serial: str) -> CdMachine | None:
        if self.machine_error is not None:
            raise self.machine_error
        return self.machine

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

    async def get_supply_description(self, supply_id: int) -> str:
        self.description_calls.append(supply_id)
        return self.description

    async def get_supplies_for_empresa(
        self, empresa_id: str, sucursal_id: str = "", top: str = "200"
    ) -> list[CdSupply]:
        return self.supplies_for_empresa


class FakeSupplyCacheRepository:
    def __init__(self) -> None:
        self.entries: list[CachedSupply] = []
        self.get_error: Exception | None = None

    async def upsert(self, entries: list[CachedSupply]) -> None:
        self.entries.extend(entries)

    async def get_by_serial(self, serial: str, limit: int = 20) -> list[CachedSupply]:
        if self.get_error is not None:
            raise self.get_error
        matching = [e for e in self.entries if e.serial.upper() == serial.upper()]
        return sorted(matching, key=lambda e: e.supply_id, reverse=True)[:limit]

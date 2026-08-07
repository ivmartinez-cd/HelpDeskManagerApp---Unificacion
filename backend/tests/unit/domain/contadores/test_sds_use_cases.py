import uuid
from datetime import UTC, datetime

import pytest

from src.modules.contadores.application.dtos.sds_dtos import ExportSdsMetersRequest
from src.modules.contadores.application.use_cases.export_sds_meters import ExportSdsMetersUseCase
from src.modules.contadores.application.use_cases.list_sds_clients import ListSdsClientsUseCase
from src.modules.contadores.application.use_cases.update_sds_client_config import (
    UpdateSdsClientConfigUseCase,
)
from src.modules.contadores.domain.entities.meter_client_config import MeterClientConfig
from src.modules.contadores.domain.entities.sds_client import SdsClient
from src.modules.contadores.domain.value_objects.meter_source import MeterSource

# ---------------------------------------------------------------------------
# Stubs e In-Memory Repositories
# ---------------------------------------------------------------------------


class StubSdsClientProvider:
    def __init__(self, customers: list[SdsClient] | None = None) -> None:
        self.customers = customers or []
        self.exported_calls: list[dict] = []

    async def list_active_customers(self) -> list[SdsClient]:
        return self.customers

    async def export_meters_to_csv(
        self,
        *,
        customer_id: str,
        customer_name: str,
        max_date: str,
        output_dir: str,
        suma_color: bool = False,
    ) -> str:
        self.exported_calls.append(
            {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "max_date": max_date,
                "output_dir": output_dir,
                "suma_color": suma_color,
            }
        )
        return f"{output_dir}/SDS_{customer_name}_20260807_AutoCSV.csv"


class InMemoryMeterClientConfigRepository:
    def __init__(self, configs: list[MeterClientConfig] | None = None) -> None:
        self._configs: dict[tuple[MeterSource, str], MeterClientConfig] = {
            (c.source, c.customer_id): c for c in (configs or [])
        }

    async def list_by_source(self, source: MeterSource) -> list[MeterClientConfig]:
        return [c for (src, _), c in self._configs.items() if src == source]

    async def get(self, source: MeterSource, customer_id: str) -> MeterClientConfig | None:
        return self._configs.get((source, customer_id))

    async def upsert(
        self, *, source: MeterSource, customer_id: str, customer_name: str, suma_color: bool
    ) -> MeterClientConfig:
        config = MeterClientConfig(
            id=uuid.uuid4(),
            source=source,
            customer_id=customer_id,
            customer_name=customer_name,
            suma_color=suma_color,
            updated_at=datetime.now(UTC),
        )
        self._configs[(source, customer_id)] = config
        return config


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sds_clients_merges_config() -> None:
    provider = StubSdsClientProvider(
        [
            SdsClient(id="101", name="Cliente A"),
            SdsClient(id="102", name="Cliente B"),
        ]
    )
    config_repo = InMemoryMeterClientConfigRepository(
        [
            MeterClientConfig(
                id=uuid.uuid4(),
                source=MeterSource("sds"),
                customer_id="101",
                customer_name="Cliente A",
                suma_color=True,
                updated_at=datetime.now(UTC),
            )
        ]
    )

    use_case = ListSdsClientsUseCase(provider, config_repo)
    results = await use_case.execute()

    assert len(results) == 2
    assert results[0].id == "101"
    assert results[0].suma_color is True
    assert results[1].id == "102"
    assert results[1].suma_color is False


@pytest.mark.asyncio
async def test_update_sds_client_config_persists_preference() -> None:
    config_repo = InMemoryMeterClientConfigRepository()
    use_case = UpdateSdsClientConfigUseCase(config_repo)

    result = await use_case.execute(
        customer_id="101",
        customer_name="Cliente A",
        suma_color=True,
    )

    assert result.id == "101"
    assert result.suma_color is True

    saved = await config_repo.get(MeterSource("sds"), "101")
    assert saved is not None
    assert saved.suma_color is True


@pytest.mark.asyncio
async def test_export_sds_meters_passes_suma_color_preference() -> None:
    provider = StubSdsClientProvider()
    config_repo = InMemoryMeterClientConfigRepository(
        [
            MeterClientConfig(
                id=uuid.uuid4(),
                source=MeterSource("sds"),
                customer_id="101",
                customer_name="Cliente A",
                suma_color=True,
                updated_at=datetime.now(UTC),
            )
        ]
    )

    use_case = ExportSdsMetersUseCase(provider, config_repo)
    request = ExportSdsMetersRequest(
        customer_id="101",
        customer_name="Cliente A",
        max_date="2026-08-07T00:00:00",
        output_dir="/tmp/output",
    )

    result = await use_case.execute(request)

    assert result.customer_name == "Cliente A"
    assert result.filename == "SDS_Cliente A_20260807_AutoCSV.csv"
    assert len(provider.exported_calls) == 1
    assert provider.exported_calls[0]["suma_color"] is True

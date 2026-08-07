import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.contadores.domain.entities.meter_client_config import MeterClientConfig
from src.modules.contadores.domain.value_objects.meter_source import MeterSource
from src.modules.contadores.infrastructure.models.meter_client_config_model import (
    MeterClientConfigModel,
)


class SqlAlchemyMeterClientConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_source(self, source: MeterSource) -> list[MeterClientConfig]:
        stmt = select(MeterClientConfigModel).where(MeterClientConfigModel.source == source.value)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(row) for row in rows]

    async def get(self, source: MeterSource, customer_id: str) -> MeterClientConfig | None:
        stmt = select(MeterClientConfigModel).where(
            MeterClientConfigModel.source == source.value,
            MeterClientConfigModel.customer_id == customer_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model else None

    async def upsert(
        self, *, source: MeterSource, customer_id: str, customer_name: str, suma_color: bool
    ) -> MeterClientConfig:
        stmt = select(MeterClientConfigModel).where(
            MeterClientConfigModel.source == source.value,
            MeterClientConfigModel.customer_id == customer_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            model = MeterClientConfigModel(
                id=uuid.uuid4(),
                source=source.value,
                customer_id=customer_id,
                customer_name=customer_name,
                suma_color=suma_color,
            )
            self._session.add(model)
        else:
            model.customer_name = customer_name
            model.suma_color = suma_color
        await self._session.flush()
        return _to_entity(model)


def _to_entity(model: MeterClientConfigModel) -> MeterClientConfig:
    return MeterClientConfig(
        id=model.id,
        source=MeterSource(model.source),
        customer_id=model.customer_id,
        customer_name=model.customer_name,
        suma_color=model.suma_color,
        updated_at=model.updated_at,
    )

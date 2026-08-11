"""Implementación Postgres del puerto ZoneContactRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.zone_contacts import ZoneContacts
from src.modules.insumos.infrastructure.models.customer_zone_contact_model import (
    CustomerZoneContactModel,
)


class SqlAlchemyZoneContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, customer_id: int, zone: str) -> ZoneContacts | None:
        stmt = select(CustomerZoneContactModel).where(
            CustomerZoneContactModel.customer_id == customer_id,
            CustomerZoneContactModel.zone == zone,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return ZoneContacts(
            solicitante=ContactInfo(
                apellido=row.sol_apellido,
                nombre=row.sol_nombre,
                telefono=row.sol_telefono,
                email=row.sol_email,
                sector=row.sol_sector,
            ),
            destinatario=ContactInfo(
                apellido=row.dest_apellido,
                nombre=row.dest_nombre,
                telefono=row.dest_telefono,
                email=row.dest_email,
                sector=row.dest_sector,
            ),
            observaciones=row.observaciones,
        )

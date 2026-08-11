"""Implementación Postgres del puerto ZoneContactRepository."""

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.domain.value_objects.order_request import ContactInfo
from src.modules.insumos.domain.value_objects.zone_contacts import (
    ZoneContactRow,
    ZoneContacts,
)
from src.modules.insumos.infrastructure.models.customer_zone_contact_model import (
    CustomerZoneContactModel,
)

_CONTACT_COLS = [
    "sol_apellido", "sol_nombre", "sol_telefono", "sol_email", "sol_sector",
    "dest_apellido", "dest_nombre", "dest_telefono", "dest_email", "dest_sector",
    "observaciones",
]


def _to_zone_contact_row(row: CustomerZoneContactModel) -> ZoneContactRow:
    return ZoneContactRow(
        zone=row.zone,
        sol_apellido=row.sol_apellido,
        sol_nombre=row.sol_nombre,
        sol_telefono=row.sol_telefono,
        sol_email=row.sol_email,
        sol_sector=row.sol_sector,
        dest_apellido=row.dest_apellido,
        dest_nombre=row.dest_nombre,
        dest_telefono=row.dest_telefono,
        dest_email=row.dest_email,
        dest_sector=row.dest_sector,
        observaciones=row.observaciones,
    )


def _row_to_dict(customer_id: int, row: ZoneContactRow) -> dict:  # type: ignore[type-arg]
    return {
        "customer_id": customer_id,
        "zone": row.zone,
        "sol_apellido": row.sol_apellido,
        "sol_nombre": row.sol_nombre,
        "sol_telefono": row.sol_telefono,
        "sol_email": row.sol_email,
        "sol_sector": row.sol_sector,
        "dest_apellido": row.dest_apellido,
        "dest_nombre": row.dest_nombre,
        "dest_telefono": row.dest_telefono,
        "dest_email": row.dest_email,
        "dest_sector": row.dest_sector,
        "observaciones": row.observaciones,
    }


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

    async def list_all(self, customer_id: int) -> list[ZoneContactRow]:
        stmt = (
            select(CustomerZoneContactModel)
            .where(CustomerZoneContactModel.customer_id == customer_id)
            .order_by(
                case((CustomerZoneContactModel.zone == "", 1), else_=0),
                CustomerZoneContactModel.zone,
            )
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_zone_contact_row(r) for r in rows]

    async def upsert(self, customer_id: int, row: ZoneContactRow) -> None:
        stmt = insert(CustomerZoneContactModel).values(_row_to_dict(customer_id, row))
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id", "zone"],
            set_={col: getattr(stmt.excluded, col) for col in _CONTACT_COLS},
        )
        await self._session.execute(stmt)

    async def delete(self, customer_id: int, zone: str) -> None:
        await self._session.execute(
            delete(CustomerZoneContactModel).where(
                CustomerZoneContactModel.customer_id == customer_id,
                CustomerZoneContactModel.zone == zone,
            )
        )

    async def bulk_set(self, customer_ids: list[int], row: ZoneContactRow) -> int:
        if not customer_ids:
            return 0
        values = [_row_to_dict(cid, row) for cid in customer_ids]
        stmt = insert(CustomerZoneContactModel).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id", "zone"],
            set_={col: getattr(stmt.excluded, col) for col in _CONTACT_COLS},
        )
        await self._session.execute(stmt)
        return len(customer_ids)

    async def customers_with_contacts(self) -> set[int]:
        stmt = (
            select(CustomerZoneContactModel.customer_id)
            .where(
                or_(
                    func.length(CustomerZoneContactModel.sol_apellido) > 0,
                    func.length(CustomerZoneContactModel.sol_nombre) > 0,
                    func.length(CustomerZoneContactModel.dest_apellido) > 0,
                    func.length(CustomerZoneContactModel.dest_nombre) > 0,
                )
            )
            .distinct()
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return set(rows)

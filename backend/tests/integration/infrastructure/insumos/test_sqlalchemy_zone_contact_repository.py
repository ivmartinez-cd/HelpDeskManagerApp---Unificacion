"""Tests de integración de SqlAlchemyZoneContactRepository (Postgres de test)."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.insumos.infrastructure.models.customer_zone_contact_model import (
    CustomerZoneContactModel,
)
from src.modules.insumos.infrastructure.repositories.sqlalchemy_zone_contact_repository import (
    SqlAlchemyZoneContactRepository,
)


async def test_get_zona_exacta_y_zona_default(db_session: AsyncSession) -> None:
    db_session.add(
        CustomerZoneContactModel(
            customer_id=8,
            zone="HANGAR",
            sol_apellido="Cordoba",
            sol_nombre="Facundo",
            sol_telefono="123",
            sol_email="fc@e.com",
            sol_sector="",
            dest_apellido="Perez",
            dest_nombre="Ana",
            dest_telefono="456",
            dest_email="ap@e.com",
            dest_sector="",
            observaciones="entregar en Oficina Salta",
        )
    )
    db_session.add(
        CustomerZoneContactModel(
            customer_id=8,
            zone="",
            sol_apellido="Global",
            sol_nombre="",
            sol_telefono="",
            sol_email="",
            sol_sector="",
            dest_apellido="",
            dest_nombre="",
            dest_telefono="",
            dest_email="",
            dest_sector="",
            observaciones="",
        )
    )
    await db_session.flush()
    repo = SqlAlchemyZoneContactRepository(db_session)

    zona = await repo.get(8, "HANGAR")
    assert zona is not None
    assert zona.solicitante.apellido == "Cordoba"
    assert zona.observaciones == "entregar en Oficina Salta"
    assert zona.has_named_solicitante()

    default = await repo.get(8, "")
    assert default is not None
    assert default.solicitante.apellido == "Global"

    assert await repo.get(8, "OTRA") is None

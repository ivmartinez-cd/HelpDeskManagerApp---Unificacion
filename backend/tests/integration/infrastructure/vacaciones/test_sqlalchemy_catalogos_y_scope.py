import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.exclusion import Exclusion
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.infrastructure.models.config_model import VacacionesConfigModel
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_config_repository import (
    SqlAlchemyConfigRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_exclusion_repository import (
    SqlAlchemyExclusionRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_manager_repository import (  # noqa: E501
    SqlAlchemySectorManagerRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_sector_repository import (
    SqlAlchemySectorRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import make_empleado_entity


@pytest.mark.asyncio
async def test_sector_abm_sobre_department_compartida(db_session: AsyncSession) -> None:
    repo = SqlAlchemySectorRepository(db_session)
    sector = Sector(
        id=uuid.uuid4(), name=f"Logística {uuid.uuid4().hex[:6]}", color="#059669", is_active=True
    )
    await repo.add(sector)

    leido = await repo.get_by_name(sector.name)
    assert leido is not None
    assert leido.color == "#059669"

    sector.color = "#111111"
    await repo.save(sector)
    releido = await repo.get_by_id(sector.id)
    assert releido is not None
    assert releido.color == "#111111"


@pytest.mark.asyncio
async def test_exclusion_par_normalizado_y_unico(
    db_session: AsyncSession, empleado: Empleado, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
        SqlAlchemyEmpleadoRepository,
    )

    otro = make_empleado_entity(sector_id, cargo_id)
    await SqlAlchemyEmpleadoRepository(db_session).add(otro)

    a, b = sorted([empleado.id, otro.id])
    repo = SqlAlchemyExclusionRepository(db_session)
    await repo.add(Exclusion(id=uuid.uuid4(), empleado_a_id=a, empleado_b_id=b))

    por_b = await repo.list_por_empleado(b)
    assert len(por_b) == 1
    assert por_b[0].contraparte_de(b) == a

    with pytest.raises(IntegrityError):
        # Orden invertido viola el CHECK a < b (normalización en el schema).
        await repo.add(Exclusion(id=uuid.uuid4(), empleado_a_id=b, empleado_b_id=a))


@pytest.mark.asyncio
async def test_config_parsea_tiers_e_ignora_invalidos(db_session: AsyncSession) -> None:
    db_session.add(
        VacacionesConfigModel(
            id="singleton",
            seniority_tiers=[
                {"min_years": 0, "max_years": 5, "days": 14},
                {"esto": "no es un tier"},
            ],
        )
    )
    await db_session.flush()

    config = await SqlAlchemyConfigRepository(db_session).get()
    assert len(config.seniority_tiers) == 1
    assert config.seniority_tiers[0].days == 14
    assert config.next_year_open_month == 10  # server_default


@pytest.mark.asyncio
async def test_sector_manager_asignar_upsert_y_desasignar(
    db_session: AsyncSession, sector_id: uuid.UUID
) -> None:
    from src.modules.auth.infrastructure.models.permission_models import Module

    if await db_session.get(Module, "vacaciones") is None:
        db_session.add(
            Module(key="vacaciones", label="Vacaciones", route="/vacaciones", icon="calendar")
        )
    user = AppUser(
        id=uuid.uuid4(),
        email=f"jefe-{uuid.uuid4().hex[:8]}@canal.com",
        password_hash="x",
        full_name="Jefe Test",
    )
    db_session.add(user)
    await db_session.flush()

    repo = SqlAlchemySectorManagerRepository(db_session)
    await repo.asignar(user.id, sector_id)
    assert await repo.get_sector_de_usuario(user.id) == sector_id

    # Upsert: reasignar al mismo usuario cambia el sector, no duplica fila.
    await repo.asignar(user.id, sector_id)
    jefes = [j for j in await repo.list_jefes() if j.user_id == user.id]
    assert len(jefes) == 1

    await repo.desasignar(user.id)
    assert await repo.get_sector_de_usuario(user.id) is None


@pytest.mark.asyncio
async def test_empleado_user_id_unico(
    db_session: AsyncSession, sector_id: uuid.UUID, cargo_id: uuid.UUID
) -> None:
    from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
        SqlAlchemyEmpleadoRepository,
    )

    user = AppUser(
        id=uuid.uuid4(),
        email=f"cuenta-{uuid.uuid4().hex[:8]}@canal.com",
        password_hash="x",
        full_name="Cuenta Test",
    )
    db_session.add(user)
    await db_session.flush()

    repo = SqlAlchemyEmpleadoRepository(db_session)
    await repo.add(make_empleado_entity(sector_id, cargo_id, user_id=user.id))
    vinculado = await repo.get_by_user_id(user.id)
    assert vinculado is not None
    assert vinculado.hire_date == date(2019, 3, 15)

    with pytest.raises(IntegrityError):
        await repo.add(make_empleado_entity(sector_id, cargo_id, user_id=user.id))

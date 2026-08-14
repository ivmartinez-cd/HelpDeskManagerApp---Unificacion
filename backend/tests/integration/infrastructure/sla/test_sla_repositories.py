"""Round-trips del snapshot SLA y del lookup de PST por operador (incluye la
resolución de overrides de ADR-013) contra Postgres de test."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import AppUser
from src.modules.prestadores.domain.entities.asignacion_override import AsignacionOverride
from src.modules.prestadores.domain.entities.prestador import Prestador
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_asignacion_override_repository import (  # noqa: E501
    SqlAlchemyAsignacionOverrideRepository,
)
from src.modules.prestadores.infrastructure.repositories.sqlalchemy_prestador_repository import (
    SqlAlchemyPrestadorRepository,
)
from src.modules.sla.domain.entities.incidente_sla import IncidenteSla
from src.modules.sla.domain.entities.sla_snapshot import SlaSnapshot, TecnicoVencidos
from src.modules.sla.infrastructure.repositories.sqlalchemy_prestador_lookup import (
    SqlAlchemyPrestadorLookup,
)
from src.modules.sla.infrastructure.repositories.sqlalchemy_sla_snapshot_repository import (
    SqlAlchemySlaSnapshotRepository,
)


def _incidente(id_incidente: int = 1) -> IncidenteSla:
    return IncidenteSla(
        id_incidente=id_incidente,
        fecha_ingreso=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        tipo="Correctivo",
        estado="Cerrado",
        cliente="YAGUAR",
        sucursal="Central",
        nro_serie="S1",
        modelo="M404",
        tecnico="PST Rosario",
        id_tecnico=137,
        region="Litoral",
        fecha_operativo=None,
        periodo=202608,
        tiempo="72:00",
        rango="48-96",
        sla_horas=48,
        horas_vencido=24,
        resultado="Vencido",
    )


def _snapshot(periodo: int = 202608, *, vencidos: int = 1) -> SlaSnapshot:
    return SlaSnapshot(
        periodo=periodo,
        total=10,
        correctos=10 - vencidos,
        vencidos=vencidos,
        pct_correctos=90.0,
        pct_vencidos=10.0,
        vencidos_por_tecnico=[
            TecnicoVencidos(
                tecnico="PST Rosario", id_tecnico=137, cantidad=vencidos, ids_incidente=[1]
            )
        ],
        incidentes_vencidos=[_incidente()],
        updated_at=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
    )


async def test_snapshot_upsert_y_get_round_trip(db_session: AsyncSession) -> None:
    repo = SqlAlchemySlaSnapshotRepository(db_session)
    assert await repo.get(202608) is None

    await repo.upsert(_snapshot())
    leido = await repo.get(202608)

    assert leido is not None
    assert (leido.total, leido.vencidos) == (10, 1)
    assert leido.vencidos_por_tecnico[0].id_tecnico == 137
    incidente = leido.incidentes_vencidos[0]
    assert incidente.id_incidente == 1
    assert incidente.fecha_ingreso is not None and incidente.fecha_operativo is None
    assert incidente.resultado == "Vencido"


async def test_snapshot_upsert_pisa_el_periodo_existente(db_session: AsyncSession) -> None:
    repo = SqlAlchemySlaSnapshotRepository(db_session)
    await repo.upsert(_snapshot(vencidos=1))

    await repo.upsert(_snapshot(vencidos=3))

    leido = await repo.get(202608)
    assert leido is not None and leido.vencidos == 3


async def _operador(session: AsyncSession, nombre: str) -> uuid.UUID:
    user = AppUser(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.local",
        password_hash="x",
        full_name=nombre,
    )
    session.add(user)
    await session.flush()
    return user.id


async def _prestador(session: AsyncSession, siges_id: int, operador_id: uuid.UUID) -> Prestador:
    prestador = Prestador(
        id=uuid.uuid4(),
        siges_empresa_id=siges_id,
        den_comercial=f"PST {siges_id}",
        razon_social=None,
        cuit=None,
        equipos=None,
        operador_id=operador_id,
        is_active=True,
    )
    await SqlAlchemyPrestadorRepository(session).add(prestador)
    return prestador


async def test_lookup_sin_overrides_devuelve_los_propios(db_session: AsyncSession) -> None:
    juan = await _operador(db_session, "Juan")
    pedro = await _operador(db_session, "Pedro")
    await _prestador(db_session, 137, juan)
    await _prestador(db_session, 205, juan)
    await _prestador(db_session, 300, pedro)

    lookup = SqlAlchemyPrestadorLookup(db_session)

    assert await lookup.get_siges_ids_por_operador(juan) == [137, 205]
    assert await lookup.get_siges_ids_por_operador(pedro) == [300]


async def test_lookup_con_override_total_mueve_la_cartera_al_reemplazante(
    db_session: AsyncSession,
) -> None:
    juan = await _operador(db_session, "Juan")
    pedro = await _operador(db_session, "Pedro")
    await _prestador(db_session, 137, juan)
    hoy = date.today()
    await SqlAlchemyAsignacionOverrideRepository(db_session).create(
        AsignacionOverride(
            id=uuid.uuid4(),
            operador_ausente_id=juan,
            operador_reemplazante_id=pedro,
            desde=hoy,
            hasta=hoy,
            alcance="TOTAL",
            estado="ACTIVA",
            motivo="vacaciones",
            created_by_user_id=pedro,
        )
    )

    lookup = SqlAlchemyPrestadorLookup(db_session)

    # El ausente deja de ver su cartera cubierta; el reemplazante la suma.
    assert await lookup.get_siges_ids_por_operador(juan) == []
    assert await lookup.get_siges_ids_por_operador(pedro) == [137]

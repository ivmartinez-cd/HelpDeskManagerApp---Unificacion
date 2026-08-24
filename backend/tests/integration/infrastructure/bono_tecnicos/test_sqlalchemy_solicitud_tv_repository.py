"""SqlAlchemySolicitudTvRepository contra Postgres real: alta, decisión y
conteo de aprobadas por período — la fuente del TV que usa GetPuntajesPeriodo."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.bono_tecnicos.domain.entities.solicitud_tv import EstadoSolicitudTv, SolicitudTv
from src.modules.bono_tecnicos.domain.value_objects.periodo import Periodo
from src.modules.bono_tecnicos.infrastructure.repositories.sqlalchemy_solicitud_tv_repository import (  # noqa: E501
    SqlAlchemySolicitudTvRepository,
)


def _id_tecnico() -> int:
    return uuid.uuid4().int % 1_000_000_000


def _solicitud(id_tecnico: int, fecha: date = date(2026, 5, 18)) -> SolicitudTv:
    return SolicitudTv(
        id=uuid.uuid4(),
        id_tecnico=id_tecnico,
        tecnico="CD - Ana",
        fecha=fecha,
        razon_social="Exolgan",
        sucursal="Dock Sur",
        tarea_realizada="Se buscan toner en Drago y se llevan a Exolgan.",
        estado=EstadoSolicitudTv.PENDIENTE,
        creado_en=datetime.now(UTC),
    )


async def test_add_y_get_by_id(db_session: AsyncSession) -> None:
    repo = SqlAlchemySolicitudTvRepository(db_session)
    solicitud = _solicitud(_id_tecnico())

    await repo.add(solicitud)
    guardada = await repo.get_by_id(solicitud.id)

    assert guardada is not None
    assert guardada.estado is EstadoSolicitudTv.PENDIENTE
    assert guardada.razon_social == "Exolgan"


async def test_save_persiste_la_decision(db_session: AsyncSession) -> None:
    repo = SqlAlchemySolicitudTvRepository(db_session)
    solicitud = _solicitud(_id_tecnico())
    await repo.add(solicitud)

    solicitud.aprobar(datetime.now(UTC), "supervisor@canaldirecto.com.ar")
    await repo.save(solicitud)

    guardada = await repo.get_by_id(solicitud.id)
    assert guardada is not None
    assert guardada.estado is EstadoSolicitudTv.APROBADA
    assert guardada.resuelta_por_email == "supervisor@canaldirecto.com.ar"


async def test_list_by_periodo_filtra_estado_y_tecnico(db_session: AsyncSession) -> None:
    repo = SqlAlchemySolicitudTvRepository(db_session)
    id_tecnico = _id_tecnico()
    pendiente = _solicitud(id_tecnico)
    de_otro_tecnico = _solicitud(_id_tecnico())
    await repo.add(pendiente)
    await repo.add(de_otro_tecnico)

    result = await repo.list_by_periodo(
        Periodo(202605), estado=EstadoSolicitudTv.PENDIENTE, id_tecnico=id_tecnico
    )

    assert [s.id for s in result] == [pendiente.id]


async def test_count_aprobadas_por_tecnico_solo_cuenta_aprobadas(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemySolicitudTvRepository(db_session)
    id_tecnico = _id_tecnico()
    for _ in range(3):
        s = _solicitud(id_tecnico)
        await repo.add(s)
        s.aprobar(datetime.now(UTC), "supervisor@canaldirecto.com.ar")
        await repo.save(s)
    pendiente = _solicitud(id_tecnico)
    await repo.add(pendiente)

    conteo = await repo.count_aprobadas_por_tecnico(Periodo(202605))

    assert conteo[id_tecnico] == 3

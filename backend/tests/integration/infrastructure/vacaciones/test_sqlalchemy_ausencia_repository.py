"""SqlAlchemyAusenciaRepository contra Postgres real: round trip, filtros
combinables, solapamiento (solo PENDING/APPROVED) y save/delete idempotentes."""

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.models.user_model import Department
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.solicitud import EstadoSolicitud
from src.modules.vacaciones.domain.repositories.ausencia_repository import FiltrosAusencias
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_ausencia_repository import (
    SqlAlchemyAusenciaRepository,
)
from src.modules.vacaciones.infrastructure.repositories.sqlalchemy_empleado_repository import (
    SqlAlchemyEmpleadoRepository,
)
from tests.integration.infrastructure.vacaciones.conftest import make_empleado_entity


def _ausencia(
    empleado_id: uuid.UUID,
    start: date,
    end: date,
    *,
    tipo: TipoAusencia = TipoAusencia.BAJA_ENFERMEDAD,
    status: EstadoSolicitud = EstadoSolicitud.APPROVED,
    hora_desde: time | None = None,
    hora_hasta: time | None = None,
) -> Ausencia:
    return Ausencia(
        id=uuid.uuid4(),
        empleado_id=empleado_id,
        start_date=start,
        end_date=end,
        days_count=(end - start).days + 1,
        half_day=False,
        tipo=tipo,
        reason="motivo",
        status=status,
        created_at=datetime.now(UTC),
        hora_desde=hora_desde,
        hora_hasta=hora_hasta,
    )


async def test_add_y_get_by_id_round_trip_con_horario(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyAusenciaRepository(db_session)
    cambio = _ausencia(
        empleado.id,
        date(2026, 10, 5),
        date(2026, 10, 9),
        tipo=TipoAusencia.CAMBIO_HORARIO,
        hora_desde=time(8, 0),
        hora_hasta=time(17, 0),
    )
    await repo.add(cambio)

    leida = await repo.get_by_id(cambio.id)
    assert leida is not None
    assert leida.tipo is TipoAusencia.CAMBIO_HORARIO
    assert leida.horario_texto == "08:00–17:00"
    assert leida.days_count == 5
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_list_filtradas_combina_filtros_y_ordena_desc(
    db_session: AsyncSession, empleado: Empleado, sector_id: uuid.UUID
) -> None:
    repo = SqlAlchemyAusenciaRepository(db_session)
    otro_sector = Department(id=uuid.uuid4(), name=f"Otro {uuid.uuid4().hex[:8]}")
    db_session.add(otro_sector)
    await db_session.flush()
    ajeno = make_empleado_entity(otro_sector.id, empleado.cargo_id)
    await SqlAlchemyEmpleadoRepository(db_session).add(ajeno)

    vieja = _ausencia(empleado.id, date(2026, 3, 2), date(2026, 3, 3))
    nueva = _ausencia(
        empleado.id, date(2026, 6, 1), date(2026, 6, 1), tipo=TipoAusencia.HOME_OFFICE,
        status=EstadoSolicitud.PENDING,
    )
    de_otro = _ausencia(ajeno.id, date(2026, 4, 1), date(2026, 4, 1))
    for a in (vieja, nueva, de_otro):
        await repo.add(a)

    del_sector = await repo.list_filtradas(FiltrosAusencias(department_id=sector_id))
    assert [a.id for a in del_sector] == [nueva.id, vieja.id]

    assert [
        a.id for a in await repo.list_filtradas(FiltrosAusencias(status=EstadoSolicitud.PENDING))
    ] == [nueva.id]
    assert [
        a.id
        for a in await repo.list_filtradas(
            FiltrosAusencias(tipo=TipoAusencia.BAJA_ENFERMEDAD, empleado_id=empleado.id)
        )
    ] == [vieja.id]
    rango = await repo.list_filtradas(
        FiltrosAusencias(desde=date(2026, 3, 15), hasta=date(2026, 4, 30))
    )
    assert [a.id for a in rango] == [de_otro.id]


async def test_existe_activa_solapada_ignora_rechazadas_otro_tipo_y_excluida(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyAusenciaRepository(db_session)
    aprobada = _ausencia(empleado.id, date(2026, 9, 7), date(2026, 9, 11))
    await repo.add(aprobada)
    await repo.add(
        _ausencia(
            empleado.id, date(2026, 9, 20), date(2026, 9, 22), status=EstadoSolicitud.REJECTED
        )
    )

    tipo = TipoAusencia.BAJA_ENFERMEDAD
    assert await repo.existe_activa_solapada(
        empleado.id, tipo, date(2026, 9, 11), date(2026, 9, 15)
    )
    assert not await repo.existe_activa_solapada(
        empleado.id, tipo, date(2026, 9, 12), date(2026, 9, 15)
    )
    assert not await repo.existe_activa_solapada(
        empleado.id, TipoAusencia.GUARDIA, date(2026, 9, 8), date(2026, 9, 8)
    )
    assert not await repo.existe_activa_solapada(
        empleado.id, tipo, date(2026, 9, 20), date(2026, 9, 21)
    )
    assert not await repo.existe_activa_solapada(
        empleado.id, tipo, date(2026, 9, 8), date(2026, 9, 8), excluir_ausencia_id=aprobada.id
    )


async def test_list_aprobadas_solapadas_excluye_pending_y_lista_vacia(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyAusenciaRepository(db_session)
    aprobada = _ausencia(empleado.id, date(2026, 9, 7), date(2026, 9, 11))
    await repo.add(aprobada)
    await repo.add(
        _ausencia(
            empleado.id, date(2026, 9, 8), date(2026, 9, 9),
            tipo=TipoAusencia.HOME_OFFICE, status=EstadoSolicitud.PENDING,
        )
    )

    inicio, fin = date(2026, 9, 1), date(2026, 9, 30)
    assert await repo.list_aprobadas_solapadas_de_empleados([], inicio, fin) == []
    resultado = await repo.list_aprobadas_solapadas_de_empleados([empleado.id], inicio, fin)
    assert [a.id for a in resultado] == [aprobada.id]


async def test_save_y_delete_son_idempotentes_ante_ids_inexistentes(
    db_session: AsyncSession, empleado: Empleado
) -> None:
    repo = SqlAlchemyAusenciaRepository(db_session)
    ausencia = _ausencia(
        empleado.id, date(2026, 9, 7), date(2026, 9, 11), status=EstadoSolicitud.PENDING
    )
    await repo.add(ausencia)

    ausencia.status = EstadoSolicitud.APPROVED
    ausencia.reason = "aprobada por TL"
    await repo.save(ausencia)
    leida = await repo.get_by_id(ausencia.id)
    assert leida is not None
    assert leida.status is EstadoSolicitud.APPROVED
    assert leida.reason == "aprobada por TL"

    # Sin fila: no falla ni crea nada.
    fantasma = _ausencia(empleado.id, date(2026, 1, 1), date(2026, 1, 1))
    await repo.save(fantasma)
    assert await repo.get_by_id(fantasma.id) is None
    await repo.delete(fantasma.id)

    await repo.delete(ausencia.id)
    assert await repo.get_by_id(ausencia.id) is None
